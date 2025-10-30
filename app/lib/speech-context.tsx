"use client"

import type React from "react"
import { createContext, useContext, useState, useCallback, useRef } from "react"

interface SpeechContextType {
  isListening: boolean
  transcript: string
  isProcessing: boolean
  error: string | null
  startListening: () => Promise<void>
  stopListening: () => Promise<void>
  clearTranscript: () => void
}

const SpeechContext = createContext<SpeechContextType | undefined>(undefined)

export function SpeechProvider({ children }: { children: React.ReactNode }) {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const startListening = useCallback(async () => {
    try {
      setError(null)
      setTranscript("")
      audioChunksRef.current = []

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }

      mediaRecorder.start()
      setIsListening(true)
    } catch (err) {
      setError("Microphone access denied")
      console.error("Error accessing microphone:", err)
    }
  }, [])

  const stopListening = useCallback(async () => {
    if (!mediaRecorderRef.current) return

    setIsProcessing(true)
    try {
      mediaRecorderRef.current.stop()
      setIsListening(false)

      // Simulate ASR processing
      await new Promise((resolve) => setTimeout(resolve, 1500))

      // Mock transcription - in real app, send to ASR service
      const mockTranscripts = [
        "Transfer 500 dollars to John Doe account 1234567890",
        "Create a bill for electricity 150 dollars due next month",
        "Create a savings fund for vacation with target 5000 dollars",
        "Send money to Alice for lunch payment",
      ]

      const randomTranscript = mockTranscripts[Math.floor(Math.random() * mockTranscripts.length)]
      setTranscript(randomTranscript)

      // Stop all tracks
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop())
    } catch (err) {
      setError("Error processing audio")
      console.error("Error processing audio:", err)
    } finally {
      setIsProcessing(false)
    }
  }, [])

  const clearTranscript = useCallback(() => {
    setTranscript("")
    setError(null)
  }, [])

  return (
    <SpeechContext.Provider
      value={{ isListening, transcript, isProcessing, error, startListening, stopListening, clearTranscript }}
    >
      {children}
    </SpeechContext.Provider>
  )
}

export function useSpeech() {
  const context = useContext(SpeechContext)
  if (context === undefined) {
    throw new Error("useSpeech must be used within SpeechProvider")
  }
  return context
}
