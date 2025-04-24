"use client"

import { useState, useEffect, useRef } from "react"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { MessageSquare, Send, Mic, User } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { fetchGeminiResponse } from "../lib/gemeniapi"

export default function Conversation({ listening = false }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Good morning! This is Sahara. How are you feeling today?",
      sender: "assistant",
      timestamp: new Date(),
    },
  ])
  const [newMessage, setNewMessage] = useState("")
  const messagesEndRef = useRef(null)
  const [loading, setLoading] = useState(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (newMessage.trim()) {
      const userMessage = {
        id: messages.length + 1,
        text: newMessage,
        sender: "user",
        timestamp: new Date(),
      };
  
      setMessages([...messages, userMessage]);
      setNewMessage("");
  
      const assistantReply = await fetchGeminiResponse(newMessage);
  
      const assistantMessage = {
        id: messages.length + 2,
        text: assistantReply,
        sender: "assistant",
        timestamp: new Date(),
      };
  
      setMessages((prev) => [...prev, assistantMessage]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSendMessage()
    }
  }

  return (
    <Card className="h-[500px] flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-purple-500" />
          Conversation
        </CardTitle>
        <CardDescription>Chat with your AI companion anytime</CardDescription>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-[350px] px-4">
          <div className="space-y-4 py-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`flex gap-2 max-w-[80%] ${message.sender === "user" ? "flex-row-reverse" : ""}`}
                >
                  <Avatar className="h-8 w-8">
                    {message.sender === "assistant" ? (
                      <>
                        <AvatarImage src="/placeholder.svg" alt="AI Assistant" />
                        <AvatarFallback>AI</AvatarFallback>
                      </>
                    ) : (
                      <AvatarFallback>
                        <User className="h-4 w-4" />
                      </AvatarFallback>
                    )}
                  </Avatar>
                  <div>
                    <div
                      className={`rounded-lg p-3 ${
                        message.sender === "user"
                          ? "bg-blue-500 text-white"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      <p>{message.text}</p>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {message.timestamp.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </CardContent>

      <CardFooter className="border-t p-4">
        <div className="flex w-full items-center gap-2">
          <Input
            placeholder={listening ? "Listening..." : "Type your message..."}
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={listening}
            className="flex-1"
          />
          {listening ? (
            <Button size="icon" className="bg-green-600 hover:bg-green-700 animate-pulse">
              <Mic className="h-4 w-4" />
            </Button>
          ) : (
            <Button size="icon" onClick={handleSendMessage} disabled={loading || !newMessage.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  )
}
