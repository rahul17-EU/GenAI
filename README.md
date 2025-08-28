# ☕ BaristaBot Cafe

BaristaBot Cafe is an AI-powered coffee ordering assistant built with **Streamlit** and **Google Gemini (GenAI)**.  
It simulates a friendly barista chatbot that takes customer orders, handles modifiers, provides billing, and confirms orders.

---

## 🚀 Features
- Interactive **chat-based ordering system**
- Menu with **drinks, pastries, and modifiers**
- AI-powered natural conversation
- Automatic **order management (add, confirm, clear, summary, place)**

---

## 📦 Installation
Clone this repository:
```bash
git clone https://github.com/your-username/baristabot-cafe.git
cd baristabot-cafe
```

Install dependencies:
```bash
pip install -r cafe_requirements.txt
```

Set up your **Google API key** in `.env`:
```env
GOOGLE_API_KEY=your_api_key_here
```

---

## ▶️ Run the App
```bash
streamlit run cafe_app.py
```

---

## 💡 Creating Your Own Food Ordering App
Want to adapt this to pizza, burgers, or any food store?  
1. Update the **MENU** inside `cafe_app.py` to reflect your items.  
2. Adjust **pricing dictionaries** (`DRINK_PRICES`, `PASTRY_PRICES`, `MODIFIER_PRICES`).  
3. Modify `BARISTABOT_SYSINT` system instructions with your restaurant details.  
4. Re-run the app with `streamlit run cafe_app.py`.

---
```

---

## 📜 License
MIT License
