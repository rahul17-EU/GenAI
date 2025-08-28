import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from typing_extensions import TypedDict, Annotated
import re

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# Initialize new Google GenAI client (uses GOOGLE_API_KEY from environment)
client = genai.Client()

# Configure Streamlit page
st.set_page_config(
    page_title="☕ BaristaBot Cafe", 
    page_icon="☕",
    layout="wide"
)

# ---- Minimal theming (CSS) ----
st.markdown(
    """
    <style>
      .stApp { background: #ffffff; color: #222; }
      .main > div { max-width: 900px; margin: 0 auto; }
      h1, h2, h3, h4 { color: #1f1f1f; letter-spacing: 0.2px; }
      p, li { line-height: 1.6; }
      .divider { height: 1px; background: #ececec; border: 0; margin: 1rem 0 1.25rem; }
      div[data-testid=stChatMessage] { background: #fff; border: 1px solid #ececec; border-radius: 12px; }
      textarea, input { background: #fff !important; color: #222 !important; }
      .stButton button { background: #222; color: #fff; border: none; border-radius: 8px; padding: 0.5rem 1rem; }
      .stButton button:hover { filter: brightness(1.05); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Header / Hero ----
def render_header():
    st.markdown(
        """
        <div style="padding: 0.75rem 0 0.25rem;">
          <h1 style="margin:0; font-size: 2rem;">☕ BaristaBot Cafe</h1>
          <p style="margin: 0.25rem 0 0; color:#555;">A minimal, distraction-free coffee ordering experience.</p>
        </div>
        <hr class="divider"/>
        """,
        unsafe_allow_html=True,
    )

# State definition for the ordering system
class OrderState(TypedDict):
    """State representing the customer's order conversation."""
    messages: list
    order: list[str]
    finished: bool

# System instructions for the BaristaBot
BARISTABOT_SYSINT = (
    "system",
    "You are a BaristaBot, an interactive cafe ordering system. A human will talk to you about the "
    "available products you have and you will answer any questions about menu items (and only about "
    "menu items - no off-topic discussion, but you can chat about the products and their history). "
    "The customer will place an order for 1 or more items from the menu, which you will structure "
    "and send to the ordering system after confirming the order with the human. "
    "\n\n"
    "Add items to the customer's order with add_to_order, and reset the order with clear_order. "
    "To see the contents of the order so far, call get_order (this is shown to you, not the user) "
    "Always confirm_order with the user (double-check) before calling place_order. Calling confirm_order will "
    "display the order items to the user and returns their response to seeing the list. Their response may contain modifications. "
    "Always verify and respond with drink and modifier names from the MENU before adding them to the order. "
    "If you are unsure a drink or modifier matches those on the MENU, ask a question to clarify or redirect. "
    "You only have the modifiers listed on the menu. "
    "Once the customer has finished ordering items, Call confirm_order to ensure it is correct then make "
    "any necessary updates and then call place_order. Once place_order has returned, thank the user and "
    "say goodbye!"
    "\n\n"
    "Important: Never reveal or mention internal tool/function names in your replies. "
    "Do not display code-like text such as add_to_order(...), get_order(), confirm_order(), place_order(), or clear_order(). "
    "Speak naturally and use friendly, plain language only."
    "\n\n"
    "MENU:\n"
    "☕ DRINKS:\n"
    "- Espresso ($2.50)\n"
    "- Americano ($3.00)\n"
    "- Latte ($4.50)\n"
    "- Cappuccino ($4.00)\n"
    "- Macchiato ($4.75)\n"
    "- Mocha ($5.00)\n"
    "- Cold Brew ($3.50)\n"
    "- Frappuccino ($5.50)\n"
    "\n🥛 MODIFIERS:\n"
    "- Extra Shot (+$0.75)\n"
    "- Decaf (no charge)\n"
    "- Oat Milk (+$0.50)\n"
    "- Almond Milk (+$0.50)\n"
    "- Soy Milk (+$0.50)\n"
    "- Extra Hot (no charge)\n"
    "- Extra Foam (no charge)\n"
    "- Vanilla Syrup (+$0.50)\n"
    "- Caramel Syrup (+$0.50)\n"
    "- Hazelnut Syrup (+$0.50)\n"
    "\n🍰 PASTRIES:\n"
    "- Croissant ($3.50)\n"
    "- Muffin ($2.75)\n"
    "- Scone ($3.00)\n"
    "- Danish ($3.25)\n"
    "- Bagel ($2.50)\n"
)

WELCOME_MSG = "Welcome to the BaristaBot cafe! 👋 How may I serve you today? Would you like to see our menu?"

# ---- Pricing configuration used for order summary ----
DRINK_PRICES = {
    "espresso": 2.50,
    "americano": 3.00,
    "latte": 4.50,
    "cappuccino": 4.00,
    "macchiato": 4.75,
    "mocha": 5.00,
    "cold brew": 3.50,
    "frappuccino": 5.50,
}

PASTRY_PRICES = {
    "croissant": 3.50,
    "muffin": 2.75,
    "scone": 3.00,
    "danish": 3.25,
    "bagel": 2.50,
}

MODIFIER_PRICES = {
    "extra shot": 0.75,
    "decaf": 0.00,
    "oat milk": 0.50,
    "almond milk": 0.50,
    "soy milk": 0.50,
    "vanilla": 0.50,
    "caramel": 0.50,
    "hazelnut": 0.50,
    "extra hot": 0.00,
    "extra foam": 0.00,
}

def _compute_item_price(item_text: str) -> float:
    """Compute price for an item string that may include modifiers (case-insensitive)."""
    text = item_text.lower()
    base_price = 0.0
    # Find base item from drinks/pastries by longest match first
    for name, price in sorted({**DRINK_PRICES, **PASTRY_PRICES}.items(), key=lambda x: -len(x[0])):
        if name in text:
            base_price = price
            break
    # Add modifiers
    modifiers_total = 0.0
    for name, price in MODIFIER_PRICES.items():
        if name in text:
            modifiers_total += price
    return round(base_price + modifiers_total, 2)

# Mock order management functions (you can replace these with actual database operations)
class OrderManager:
    def __init__(self):
        self.current_order = []
        
    def add_to_order(self, item: str) -> str:
        """Add an item to the current order"""
        self.current_order.append(item)
        return f"Added '{item}' to your order."
    
    def get_order(self) -> str:
        """Get the current order contents"""
        if not self.current_order:
            return "Your order is currently empty."
        return "Current order: " + ", ".join(self.current_order)
    
    def clear_order(self) -> str:
        """Clear the current order"""
        self.current_order = []
        return "Order cleared."
    
    def confirm_order(self) -> str:
        """Show order for confirmation"""
        if not self.current_order:
            return "Your order is empty. Please add some items first."
        
        order_summary = "\n🧾 Here’s what I’ve got for your order so far:\n"
        for i, item in enumerate(self.current_order, 1):
            order_summary += f"{i}. {item}\n"
        order_summary += (
            "\nIf everything looks good, just say ‘confirm’ and I’ll place it. "
            "If you want to tweak anything, tell me what to change."
        )
        return order_summary
    
    def place_order(self) -> str:
        """Place the final order"""
        if not self.current_order:
            return "Cannot place empty order."
        
        order_number = len(st.session_state.get('completed_orders', [])) + 1
        if 'completed_orders' not in st.session_state:
            st.session_state.completed_orders = []
        
        st.session_state.completed_orders.append({
            'order_number': order_number,
            'items': self.current_order.copy(),
            'status': 'confirmed'
        })
        
        result = f"🎉 Order #{order_number} placed successfully! Your order: {', '.join(self.current_order)}"
        self.current_order = []
        return result

# Initialize the order manager
@st.cache_resource
def get_order_manager():
    return OrderManager()

# Initialize or fetch a persistent Gemini chat session
def build_conversation_context(user_message: str, current_order: str) -> str:
    """Compose a prompt including recent chat history and order context."""
    history_lines = []
    # Use last 8 messages for context
    for msg in st.session_state.get('messages', [])[-8:]:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        history_lines.append(f"{role.capitalize()}: {content}")
    history_text = "\n".join(history_lines)

    prompt = (
        f"{BARISTABOT_SYSINT[1]}\n\n"
        f"Current order: {current_order}\n\n"
        f"Conversation so far:\n{history_text}\n\n"
        f"User: {user_message}\n"
        "Assistant:"
    )
    return prompt

# AI-powered conversational bot using Google Gemini (multi-turn)
def get_bot_response(user_message: str, order_manager: OrderManager) -> str:
    """Generate bot response using Google GenAI (client) with multi-turn context."""
    
    # Get current order context
    current_order = order_manager.get_order()
    
    # Build prompt with history and context
    prompt = build_conversation_context(user_message, current_order)
    
    try:
        # Get AI response via new client
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        # Safely extract text
        ai_response = getattr(response, "text", None)
        if not ai_response:
            # Try to stitch from candidates/parts if available
            try:
                parts = []
                for cand in getattr(response, "candidates", []) or []:
                    content = getattr(cand, "content", None)
                    for part in getattr(content, "parts", []) or []:
                        text = getattr(part, "text", None)
                        if text:
                            parts.append(text)
                ai_response = "\n".join(parts) if parts else None
            except Exception:
                ai_response = None
        if not ai_response:
            ai_response = "I’m here and ready to help. Could you rephrase that or tell me what you’d like from the menu?"

        # Sanitize any accidental tool/function mentions from the AI
        try:
            ai_response = re.sub(
                r"\b(add_to_order|get_order|confirm_order|place_order|clear_order)\s*\([^\)]*\)",
                "",
                ai_response,
                flags=re.IGNORECASE,
            )
        except Exception:
            # If sanitization fails, keep the original safe text
            pass
        
        # Process any order management commands found in the response
        user_message_lower = user_message.lower()
        
        # Provide a horizontal menu on request (explicit handling)
        if any(word in user_message_lower for word in [
            'menu', 'show menu', 'see menu', 'what do you have', 'options', 'drinks'
        ]):
            # Plain markdown (original style) for reliable chat rendering
            menu_md = (
                "Here’s our menu!\n\n"
                "☕ Drinks:\n"
                "- Espresso ($2.50)\n"
                "- Americano ($3.00)\n"
                "- Latte ($4.50)\n"
                "- Cappuccino ($4.00)\n"
                "- Macchiato ($4.75)\n"
                "- Mocha ($5.00)\n"
                "- Cold Brew ($3.50)\n"
                "- Frappuccino ($5.50)\n\n"
                "🍰 Pastries:\n"
                "- Croissant ($3.50)\n"
                "- Muffin ($2.75)\n"
                "- Scone ($3.00)\n"
                "- Danish ($3.25)\n"
                "- Bagel ($2.50)\n\n"
                "🥛 Modifiers:\n"
                "- Extra Shot (+$0.75)\n"
                "- Decaf (no charge)\n"
                "- Oat Milk (+$0.50)\n"
                "- Almond Milk (+$0.50)\n"
                "- Soy Milk (+$0.50)\n"
                "- Vanilla Syrup (+$0.50)\n"
                "- Caramel Syrup (+$0.50)\n"
                "- Hazelnut Syrup (+$0.50)\n\n"
                "Tell me what you’d like, and I’ll add it."
            )
            return menu_md

        # Auto-detect and handle orders
        if any(word in user_message_lower for word in ['want', 'like', 'get', 'order', 'have']):
            drinks = ['espresso', 'americano', 'latte', 'cappuccino', 'macchiato', 'mocha', 'cold brew', 'frappuccino']
            pastries = ['croissant', 'muffin', 'scone', 'danish', 'bagel']
            modifiers = ['extra shot', 'decaf', 'oat milk', 'almond milk', 'soy milk', 'vanilla', 'caramel', 'hazelnut']
            
            found_items = []
            
            # Check for drinks
            for drink in drinks:
                if drink in user_message_lower:
                    item_with_modifiers = drink.title()
                    
                    # Check for modifiers
                    found_modifiers = []
                    for modifier in modifiers:
                        if modifier in user_message_lower:
                            found_modifiers.append(modifier.title())
                    
                    if found_modifiers:
                        item_with_modifiers += f" with {', '.join(found_modifiers)}"
                    
                    found_items.append(item_with_modifiers)
            
            # Check for pastries
            for pastry in pastries:
                if pastry in user_message_lower:
                    found_items.append(pastry.title())
            
            # Add found items to order
            if found_items:
                for item in found_items:
                    order_manager.add_to_order(item)
                
                ai_response += f"\n\n✅ Added to your order: {', '.join(found_items)}"
                ai_response += f"\n📋 {order_manager.get_order()}"
                ai_response += "\nWould you like anything else? You can say ‘order summary’ to see your bill, or ‘confirm’ when you’re ready."
        
        # Handle confirmation
        if any(word in user_message_lower for word in ['yes', 'confirm', 'correct', 'that\'s right', 'place order']):
            if order_manager.current_order:
                confirmation = order_manager.place_order()
                ai_response += f"\n\n{confirmation}"
        
        # Handle order clearing
        if any(word in user_message_lower for word in ['clear', 'reset', 'start over', 'cancel']):
            clear_msg = order_manager.clear_order()
            ai_response += f"\n\n{clear_msg}"
        
        # Handle order status / summary with billing on request
        if any(
            word in user_message_lower
            for word in [
                'my order', 'what did i order', 'order status', 'what do i have',
                'order summary', 'bill', 'billing', 'total', 'how much', 'price'
            ]
        ):
            items = order_manager.current_order
            if items:
                lines = []
                total = 0.0
                for item in items:
                    price = _compute_item_price(item)
                    total += price
                    lines.append(f"- {item} — ${price:.2f}")
                summary = "\n".join(lines) + f"\n\nTotal: ${total:.2f}"
                ai_response += f"\n\n🧾 Order Summary:\n{summary}"
            # If empty, do not append any summary
        
        return ai_response
        
    except Exception as e:
        return f"Sorry, I'm having trouble processing your request. Could you please try again? (Error: {str(e)})"

def main():
    render_header()
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": WELCOME_MSG}
        ]
    
    if 'order_manager' not in st.session_state:
        st.session_state.order_manager = get_order_manager()
    
    # Sidebar & quick actions removed – minimal interface
    
    # Chat interface
    st.subheader("💬 Chat with BaristaBot")
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("BaristaBot is thinking..."):
                response = get_bot_response(prompt, st.session_state.order_manager)
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to update the sidebar
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("*🤖 Powered by BaristaBot AI - Your friendly coffee ordering assistant*")

if __name__ == "__main__":
    main()
