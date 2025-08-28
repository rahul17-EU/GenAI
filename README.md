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

## 🛠 Example Prompt for a Custom Food App
If you want to use Gemini to generate a pizza-ordering chatbot, try a prompt like:

```
You are PizzaBot, an interactive food ordering assistant. A human will ask about pizzas, sides, and drinks from the MENU below. 
Answer only about menu items. Add items to the order, confirm before checkout, and provide a summary with prices.
Once confirmed, finalize the order with a friendly goodbye.

MENU:
🍕 PIZZAS:
- Margherita ($8.00)
- Pepperoni ($9.50)
- BBQ Chicken ($10.00)

🥗 SIDES:
- Garlic Bread ($3.50)
- Salad ($4.00)

🥤 DRINKS:
- Cola ($2.00)
- Lemonade ($2.50)
```

---

## 📜 License
MIT License
