"use client"

import { useState, useEffect } from "react"
import { Mic, MicOff, Clock, Camera, CameraOff } from "lucide-react"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardFooter } from "../components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "../components/ui/avatar"
import { Badge } from "../components/ui/badge"
import { toast } from "../components/hooks/useToast"
import MedicationReminder from "../components/MedicationReminder"
import FallDetection from "../components/FallDetection"
import Conversation from "../components/conversation"
import EmergencyContacts from "../components/EmergencyContacts"
import Navbar from "./Navbar"

export default function Home() {
  const [listening, setListening] = useState(false)
  const [cameraActive, setCameraActive] = useState(false)
  const [lastActivity, setLastActivity] = useState(new Date())
  const [assistantMessage, setAssistantMessage] = useState(
    "Hello! I'm Sahara, your personal assistant. How can I help you today?",
  )

  const toggleListening = () => {
    setListening(!listening)
    if (!listening) {
      toast({
        title: "Voice assistant activated",
        description: "I'm listening now. How can I help you?",
      })
      setAssistantMessage("Hi, I'm Sahara. I'm listening. How can I help you today?")
    } else {
      setAssistantMessage("Voice assistant deactivated. Tap the microphone when you need me.")
    }
  }

  const toggleCamera = () => {
    setCameraActive(!cameraActive)
    if (!cameraActive) {
      toast({
        title: "Fall detection activated",
        description: "I'm now monitoring for potential falls.",
      })
    } else {
      toast({
        title: "Fall detection deactivated",
        description: "Fall monitoring is now off.",
      })
    }
  }

  const handleWakeUpCall = () => {
    toast({
      title: "Wake up, Sahara!",
      description: "Voice assistant activated with wake phrase.",
    })
    setListening(true)
    setAssistantMessage("Hi, I'm Sahara. I'm listening. How can I help you today?")
  }

  useEffect(() => {
    const interval = setInterval(() => {
      setLastActivity(new Date())
    }, 60000)

    return () => clearInterval(interval)
  }, [])

  return (<div>
    <Navbar/>
    <main className="flex min-h-screen flex-col items-center p-4 bg-gray-50">
      <div className="w-full max-w-4xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Avatar className="h-12 w-12">
              <AvatarImage src="/placeholder.svg?height=50&width=50" alt="AI Assistant" />
              <AvatarFallback>AI</AvatarFallback>
            </Avatar>
            <div>
              <h1 className="text-2xl font-bold">Sahara</h1>
              <p className="text-sm text-gray-500">Your personal assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={cameraActive ? "default" : "outline"} className="gap-1">
              {cameraActive ? "Monitoring Active" : "Monitoring Off"}
            </Badge>
            <Badge variant="outline" className="gap-1">
              <Clock className="h-3 w-3" />
              {lastActivity.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </Badge>
          </div>
        </div>

        <Card className="mb-6 border-green-200 shadow-sm">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <Avatar>
                <AvatarImage src="/placeholder.svg?height=40&width=40" alt="AI Assistant" />
                <AvatarFallback>AI</AvatarFallback>
              </Avatar>
              <div>
                <p className="text-lg">{assistantMessage}</p>
                <p className="text-sm text-gray-500 mt-1">Tap the microphone to speak with me</p>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between border-t bg-gray-50/50 p-4">
            <Button
              variant={listening ? "default" : "outline"}
              size="lg"
              className={`gap-2 ${listening ? "bg-green-600 hover:bg-green-700" : ""}`}
              onClick={toggleListening}
            >
              {listening ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
              {listening ? "Say 'Hey Sahara'" : "Start Listening"}
            </Button>
            <Button variant="outline" size="lg" className="gap-2" onClick={handleWakeUpCall} disabled={listening}>
              Wake Up Demo
            </Button>
            <Button
              variant={cameraActive ? "default" : "outline"}
              size="lg"
              className={`gap-2 ${cameraActive ? "bg-blue-600 hover:bg-blue-700" : ""}`}
              onClick={toggleCamera}
            >
              {cameraActive ? <Camera className="h-5 w-5" /> : <CameraOff className="h-5 w-5" />}
              {cameraActive ? "Monitoring" : "Start Monitoring"}
            </Button>
          </CardFooter>
        </Card>

        <Tabs defaultValue="reminders" className="w-full">
          <TabsList className="grid grid-cols-4 mb-4">
            <TabsTrigger value="reminders">Medications</TabsTrigger>
            <TabsTrigger value="monitoring">Fall Detection</TabsTrigger>
            <TabsTrigger value="chat">Conversation</TabsTrigger>
            <TabsTrigger value="contacts">Contacts</TabsTrigger>
          </TabsList>

          <TabsContent value="reminders">
            <MedicationReminder />
          </TabsContent>

          <TabsContent value="monitoring">
            <FallDetection active={cameraActive} />
          </TabsContent>

          <TabsContent value="chat">
            <Conversation listening={listening} />
          </TabsContent>

          <TabsContent value="contacts">
            <EmergencyContacts />
          </TabsContent>
        </Tabs>
      </div>
    </main>
  </div>
  )
}
