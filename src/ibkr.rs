use crate::broker::Broker;
use async_trait::async_trait;
use secrecy::{Secret};
use tokio::net::TcpStream;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::sync::Mutex;
use std::sync::Arc;
use byteorder::{BigEndian, WriteBytesExt};
use std::time::{SystemTime, UNIX_EPOCH};
use dashmap::DashMap;

pub struct IbkrBroker {
    pub host: String,
    pub port: u32,
    pub client_id: i32,
    api_token: Option<Secret<String>>,
    stream: Option<Arc<Mutex<TcpStream>>>,
    pub next_order_id: Arc<Mutex<i32>>,
    pub market_data: Arc<DashMap<String, f64>>,
    }


impl IbkrBroker {
    pub fn new(host: String, port: u32, client_id: i32, api_token: Option<String>) -> Self {
        let final_client_id = if client_id > 0 { client_id } else { 
            (SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() % 10000) as i32 
        };

        IbkrBroker {
            host,
            port,
            client_id: final_client_id,
            api_token: api_token.map(Secret::new),
            stream: None,
            next_order_id: Arc::new(Mutex::new(1)),
            market_data: Arc::new(DashMap::new()),
        }
    }

    pub async fn start_event_loop(&mut self) -> Result<(), String> {
        let stream_arc = self.stream.as_ref().ok_or("No active connection")?.clone();
        let id_arc = self.next_order_id.clone();
        let md_arc = self.market_data.clone();
        
        loop {
            let mut stream = stream_arc.lock().await;
            let mut len_buf = [0u8; 4];
            if let Err(e) = stream.read_exact(&mut len_buf).await {
                return Err(format!("IBKR: Socket read error: {}", e));
            }
            let len = u32::from_be_bytes(len_buf) as usize;
            let mut payload = vec![0u8; len];
            stream.read_exact(&mut payload).await.map_err(|e| e.to_string())?;
            let msg = String::from_utf8_lossy(&payload);
            let parts: Vec<&str> = msg.split('\0').collect();
            drop(stream);

            if let Some(&msg_id) = parts.first() {
                match msg_id {
                    "9" => { // Next Valid ID
                        if let Some(id_str) = parts.get(1) {
                            if let Ok(id) = id_str.parse::<i32>() {
                                let mut next_id = id_arc.lock().await;
                                *next_id = id;
                                println!("IBKR: Synced Next Valid Order ID: {}", id);
                            }
                        }
                    },
                    "4" => { // TickPrice
                        // Field 0: "4", 1: tickerId, 2: tickType, 3: price, ...
                        let ticker_id = parts.get(1).unwrap_or(&"0");
                        let tick_type = parts.get(2).unwrap_or(&"0");
                        let price = parts.get(3).unwrap_or(&"0.0");
                        
                        if *tick_type == "4" || *tick_type == "2" { // Last or Ask
                            if let Ok(p) = price.parse::<f64>() {
                                md_arc.insert(ticker_id.to_string(), p); 
                            }
                        }
                    },
                    _ => Self::dispatch_message(msg_id, &parts),
                }
            }
            tokio::task::yield_now().await;
        }
    }

    fn dispatch_message(msg_id: &str, parts: &[&str]) {
        match msg_id {
            "101" => println!("IBKR: Received AccountUpdate: {:?}", parts),
            "102" => println!("IBKR: Received OrderStatus: {:?}", parts),
            "103" => println!("IBKR: Received OpenOrder: {:?}", parts),
            "4" => {}, // Handled in loop
            _ => println!("IBKR: Received message ID {}: {:?}", msg_id, parts),
        }
    }

    async fn send_message_internal(stream_arc: &Arc<Mutex<TcpStream>>, payload: &str) -> Result<(), String> {
        let mut stream = stream_arc.lock().await;
        let mut message = Vec::new();
        WriteBytesExt::write_u32::<BigEndian>(&mut message, payload.len() as u32).map_err(|e| e.to_string())?;
        message.extend_from_slice(payload.as_bytes());
        
        stream.write_all(&message).await.map_err(|e| format!("IBKR: Failed to write to socket: {}", e))
    }

    async fn perform_handshake(&mut self) -> Result<(), String> {
        if let Some(ref stream_arc) = self.stream {
            let mut stream = stream_arc.lock().await;
            stream.write_all(b"API\0").await.map_err(|e| e.to_string())?;
            
            let handshake = "v100..175"; 
            let mut msg = Vec::new();
            WriteBytesExt::write_u32::<BigEndian>(&mut msg, handshake.len() as u32).map_err(|e| e.to_string())?;
            msg.extend_from_slice(handshake.as_bytes());
            stream.write_all(&msg).await.map_err(|e| e.to_string())?;
            drop(stream);

            let start_api = format!("71\02\0{}\0\0", self.client_id);
            Self::send_message_internal(stream_arc, &start_api).await?;

            let mut stream = stream_arc.lock().await;
            let mut len_buf = [0u8; 4];
            stream.read_exact(&mut len_buf).await.map_err(|e| e.to_string())?;
            let len = u32::from_be_bytes(len_buf) as usize;
            let mut payload = vec![0u8; len];
            stream.read_exact(&mut payload).await.map_err(|e| e.to_string())?;
            let msg = String::from_utf8_lossy(&payload);
            let parts: Vec<&str> = msg.split('\0').collect();
            println!("IBKR: Received Handshake Response: {:?}", parts);
            
            if parts.get(0) == Some(&"9") {
                if let Some(id_str) = parts.get(1) {
                    if let Ok(id) = id_str.parse::<i32>() {
                        let mut next_id = self.next_order_id.lock().await;
                        *next_id = id;
                        println!("IBKR: Synced Next Valid Order ID: {}", id);
                    }
                }
            }
            
            Ok(())
        } else {
            Err("No active connection".to_string())
        }
    }
}

#[async_trait]
impl Broker for IbkrBroker {
    async fn connect(&mut self) -> Result<(), String> {
        let addr = format!("{}:{}", self.host, self.port);
        let stream = match TcpStream::connect(&addr).await {
            Ok(s) => s,
            Err(e) => return Err(format!("CONNECTION FAILED: Could not reach IBKR at {}. Ensure IB Gateway or TWS is running and the port is correct. (Error: {})", addr, e)),
        };
        
        self.stream = Some(Arc::new(Mutex::new(stream)));
        self.perform_handshake().await?;
        
        Ok(())
    }

    async fn get_account_balance(&self) -> Result<f64, String> {
        if let Some(ref stream_arc) = self.stream {
            Self::send_message_internal(stream_arc, "6\01\0\0").await?;
        }
        Ok(0.0) 
    }

    async fn get_positions(&self) -> Result<std::collections::HashMap<String, f64>, String> {
        Ok(std::collections::HashMap::new())
    }

    async fn get_price(&self, symbol: &str) -> Result<f64, String> {
        if let Some(ref stream_arc) = self.stream {
            let ticker_id = "1";
            let request = format!("1\0{}\0{}\0STK\0SMART\0NASDAQ\0USD\0\0false\0false\0", ticker_id, symbol);
            Self::send_message_internal(stream_arc, &request).await?;
            tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
            Ok(self.market_data.get(ticker_id).map(|r| *r).unwrap_or(0.0))
        } else {
            Err("No active connection".to_string())
        }
    }

    async fn place_order(&self, symbol: &str, quantity: f64, price: f64) -> Result<String, String> {
        if let Some(ref stream_arc) = self.stream {
            let mut id_lock = self.next_order_id.lock().await;
            let order_id = *id_lock;
            *id_lock += 1;
            drop(id_lock);

            let action = if quantity > 0.0 { "BUY" } else { "SELL" };
            let qty_str = quantity.abs().to_string();
            let id_str = order_id.to_string();
            
            let mut f = vec![
                "3", &id_str, "0", symbol, "STK", "", "0", "", "", 
                "SMART", "NASDAQ", "USD", "", "", "", "", action, &qty_str, "MKT", 
                "", "", "DAY", "", "", "", "0", "", "1" 
            ];
            
            while f.len() < 165 {
                f.push("");
            }
            
            let order_msg = f.join("\0") + "\0";
            Self::send_message_internal(stream_arc, &order_msg).await?;
            
            Ok(format!("IBKR-REQ-{}", order_id))
        } else {
            Err("No active connection".to_string())
        }
    }
}
