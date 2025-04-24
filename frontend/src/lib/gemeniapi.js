import { GoogleGenAI } from "@google/genai";
import { NEXT_PUBLIC_GEMINI_API_KEY } from "./constant";
export async function fetchGeminiResponse(userMessage) {
  const API_KEY = NEXT_PUBLIC_GEMINI_API_KEY;
  
  try {
    // Initialize the Google GenAI client
    const genAI = new GoogleGenAI({ apiKey: API_KEY });
    
    // Get the model
    const response = await genAI.models.generateContent({
        model: "gemini-2.0-flash",
        contents: userMessage
      });
    
    // Get the response text
    console.log("response is",response.text) 
    return response.text
    
  } catch (error) {
    console.error("Gemini API error:", error);
    return "Something went wrong while contacting Gemini.";
  }
}