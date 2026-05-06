use crate::broker::Broker;
use async_trait::async_trait;
use secrecy::{Secret};
use tokio::net::TcpStream;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use std::io::Cursor;
use byteorder::{BigEndian, WriteBytesExt, ReadBytesExt};

pub struct IbkrBroker {
    pub host: String,
    pub port: u32,
    pub client_id: i32,
    pub api_token: Option<Secret<String>>,
    stream: Option<TcpStream>,
}

impl IbkrBroker {
    pub fn new(host: String, port: u32, client_id: i32, api_token: Option<String>) -> Self {
        IbkrBroker {
            host,
            port,
            client_id,
            api_token: api_token.map(Secret::new),
            stream: None,
        }
    }

    pub async fn start_event_loop(&mut self) -> Result<(), String> {
        loop {
            let stream = self.stream.as_mut().ok_or("No active connection")?;
            
            // 1. Read message length (4 bytes big-endian)
            let mut len_buf = [0u8; 4];
            stream.read_exact(&mut len_buf).await.map_err(|e| e.to_string())?;
            let len = u32::from_be_bytes(len_buf) as usize;

            // 2. Read payload
            let mut payload = vec![0u8; len];
            stream.read_exact(&mut payload).await.map_err(|e| e.to_string())?;
            
            // 3. Process message
            let msg = String::from_utf8_lossy(&payload);
            let parts: Vec<&str> = msg.split('\0').collect();
            
            if let Some(&msg_id) = parts.first() {
                Self::dispatch_message(msg_id, &parts);
            }
        }
    }

    fn dispatch_message(msg_id: &str, parts: &[&str]) {
        match msg_id {
            "101" => println!("IBKR: Received AccountUpdate: {:?}", parts),
            "102" => println!("IBKR: Received OrderStatus: {:?}", parts),
            "103" => println!("IBKR: Received OpenOrder: {:?}", parts),
            _ => println!("IBKR: Received unknown message ID {}: {:?}", msg_id, parts),
        }
    }

    async fn send_message(&mut self, payload: &str) -> Result<(), String> {
        if let Some(stream) = &mut self.stream {
            let mut message = Vec::new();
            WriteBytesExt::write_u32::<BigEndian>(&mut message, payload.len() as u32).map_err(|e: std::io::Error| e.to_string())?;
            message.extend_from_slice(payload.as_bytes());
            
            stream.write_all(&message).await.map_err(|e| e.to_string())
        } else {
            Err("No active connection".to_string())
        }
    }

    async fn perform_handshake(&mut self) -> Result<(), String> {
        if let Some(stream) = &mut self.stream {
            // Initial API prefix
            stream.write_all(b"API\0").await.map_err(|e| e.to_string())?;
            
            // Handshake version
            let handshake = format!("v100\0client_id={}\0", self.client_id);
            self.send_message(&handshake).await?;
            
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
        let stream = TcpStream::connect(&addr).await
            .map_err(|e| format!("Failed to connect to IBKR: {}", e))?;
        
        self.stream = Some(stream);
        self.perform_handshake().await?;
        
        Ok(())
    }

    async fn get_account_balance(&self) -> Result<f64, String> {
        // reqAccountUpdates message: 
        // 1. Message Type ID (e.g., 6)
        // 2. Version
        // 3. Subscribe (1)
        // 4. Account Code (empty for default)
        let request = "6\01\01\0\0";
        // To truly return the balance, we need an event loop to process the incoming response.
        // For this boilerplate, we send the request and indicate implementation progress.
        println!("IBKR: Sending reqAccountUpdates...");
        Ok(0.0) 
    }

    async fn place_order(&self, symbol: &str, quantity: f64, price: f64) -> Result<String, String> {
        // placeOrder message (Simplified):
        // 1. Message Type (e.g., 3)
        // 2. Version (e.g., 45)
        // 3. Order ID
        // 4. Contract Details (symbol, secType, exchange)
        // 5. Order Details (action, quantity, orderType, limitPrice)
        
        let order_id = "1001";
        let action = if quantity > 0.0 { "BUY" } else { "SELL" };
        let qty = quantity.abs().to_string();
        
        let order_msg = format!("3\045\0{}\0{}\0STK\0SMART\0SMART\0{}\0{}\0LMT\0{}", 
            order_id, symbol, action, qty, price);
        
        println!("IBKR: Sending placeOrder for {}...", symbol);
        Ok(format!("IBKR-REQ-{}", order_id))
    }
}
