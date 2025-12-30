Model-3 supports Gemini API and CLI fallback .

Environment variables:
-. env : GEMINI_API_KEY = apikey
         GEMINI_MODEL = model

 I have used flash-2.5 as a default model       

Deterministic Fallback:
If for some reason like API error, The model diagnoses directly using knowledge graph used in model2, recommendeds based on deterministic rules and probability reasoning 
