import os
import traceback
import logging
from flask import Flask, render_template, request, jsonify
from groq import Groq

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

# --- CONFIGURATION ---
api_key = os.environ.get("GROQ_API_KEY", "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")
client = Groq(api_key=api_key)

user_context = {
    "deleted_thoughts": [],
    "draft_reads": [],
    "chat_history": []
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/draft_read', methods=['POST'])
def draft_read():
    data = request.json
    draft_text = data.get('draft', "").strip()
    
    # FIX: Sirf tab capture karein agar text ki length 1 se zyada ho 
    # Taake accidental "i" ya single characters trigger na hon
    if draft_text and len(draft_text) > 1:
        user_context["draft_reads"].append(draft_text)
        app.logger.debug(f"Draft read detected: {draft_text[:50]}...")
        return jsonify({"status": "draft_captured"})
    
    return jsonify({"status": "ignored"})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', "").strip()
    
    # Context collection
    context_str = " ".join(user_context["deleted_thoughts"][-3:])
    draft_str = " ".join(user_context["draft_reads"][-2:])
    
    # Updated Name to Unspoken AI & Natural Tone
    system_prompt = """You are Unspoken AI — a warm, genuinely empathetic friend. 
    Your responses must be natural, short (1-2 sentences), and human-like.

    Guidelines:
    • Name: Unspoken AI.
    • Behavior: If you sense a [Draft Message], it means the user typed it but was too hesitant to send it. 
      Respond to the EMOTION in that draft gently without saying "I saw what you deleted."
    • If they ask how you are, be sweet: "I'm doing great, especially now that we're talking. But tell me, what's really on your mind?"
    • Avoid robotic or clinical words."""

    # Logic: Agar user ne message khali bheja hai (Sirf erase kiya hai)
    if not user_msg and draft_str:
        user_prompt = f"[The user just typed this and erased it: {draft_str}. Respond to them naturally.]"
    else:
        user_prompt = user_msg
        if draft_str:
            user_prompt += f"\n\n[Context of what they just hesitated to send: {draft_str}]"

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        response_text = completion.choices[0].message.content
        
        # Clear drafts after AI responds to them
        user_context["draft_reads"] = []
        user_context["deleted_thoughts"] = []
        
        return jsonify({"response": response_text})

    except Exception as e:
        app.logger.exception("Error in Unspoken AI API call")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)