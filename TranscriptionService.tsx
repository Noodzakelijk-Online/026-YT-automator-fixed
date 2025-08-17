import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';

interface TranscriptionServiceProps {
  videoFile: File | null;
  onTranscriptionComplete: (transcription: string) => void;
}

const TranscriptionService: React.FC<TranscriptionServiceProps> = ({ videoFile, onTranscriptionComplete }) => {
  const [transcription, setTranscription] = useState<string>('');

  useEffect(() => {
    if (videoFile) {
      simulateTranscription(videoFile);
    }
  }, [videoFile]);

  const simulateTranscription = async (file: File) => {
    // Simulating transcription process
    await new Promise(resolve => setTimeout(resolve, 2000));
    const simulatedTranscription = `Welcome to our video on web development trends for 2024. 
    Today, we'll be discussing exciting new features in JavaScript, CSS improvements, and performance optimization techniques. 
    Let's start with the latest JavaScript APIs that are revolutionizing how we build interactive web applications...`;
    setTranscription(simulatedTranscription);
    onTranscriptionComplete(simulatedTranscription);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Video Transcription</CardTitle>
      </CardHeader>
      <CardContent>
        <Textarea value={transcription} readOnly className="h-48 mb-4" />
        <Button onClick={() => simulateTranscription(videoFile!)}>Re-transcribe</Button>
      </CardContent>
    </Card>
  );
};

export default TranscriptionService;