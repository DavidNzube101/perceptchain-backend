
# PerceptChain Backend Setup

## 📦 Prerequisites

- Python 3.10+
- Git

---

## 📥 1. Clone the Repository

```bash
git clone https://github.com/DavidNzube101/perceptchain-backend.git
cd perceptchain-backend
```

---

## 📦 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## 🛠 3. Configure Environment Variables

Create a `.env` file with the following contents:

```env
HELIUS_API_KEY="your_helius_key_here"
FLASK_APP=run.py
FLASK_ENV=development
```

---

## ▶️ 4. Run the Backend Server

```bash
python run.py
```

Backend will start at:  
`http://localhost:5000`

---

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Check if backend is running |
| `GET /token-holders/<token_address>/<limit>` | Fetch top token holders |
| `GET /wallet/tokens/<wallet_address>` | Retrieve wallet's token list |
| `GET /transactions/<address>` | Fetch wallet transaction history |

---

## 🧪 Testing the API

Example test using `curl`:

```bash
curl "http://localhost:5000/token-holders/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263/10"
```

---

## 🛠 Troubleshooting

**Missing Helius Key**  
Ensure your `.env` includes:
```env
HELIUS_API_KEY="your_key_here"
```

**Port Conflicts**  
To use a different port, add this to your `.env`:
```env
PORT=8000
```

**Dependency Issues**  
Try forcing a reinstall:
```bash
pip install --force-reinstall -r requirements.txt
```
