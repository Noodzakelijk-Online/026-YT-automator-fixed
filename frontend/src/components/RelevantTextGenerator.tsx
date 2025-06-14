import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';

interface RelevantTextGeneratorProps {
  transcription: string;
  summary: string;
  onRelevantTextGenerated: (text: string) => void;
}

const RelevantTextGenerator: React.FC<RelevantTextGeneratorProps> = ({ transcription, summary, onRelevantTextGenerated }) => {
  const [relevantText, setRelevantText] = useState<string>('');

  useEffect(() => {
    if (transcription && summary) {
      generateRelevantText(transcription, summary);
    }
  }, [transcription, summary]);

  const generateRelevantText = async (transcription: string, summary: string) => {
    // Simulating relevant text generation
    await new Promise(resolve => setTimeout(resolve, 1000));
    const generatedText = `Web development is constantly evolving, and 2024 brings exciting new features that will enhance both developer productivity and user experience. From advanced JavaScript APIs to cutting-edge CSS capabilities, these innovations will shape the future of web applications. Stay ahead of the curve by mastering these new technologies and optimizing your web development workflow.`;
    setRelevantText(generatedText);
    onRelevantTextGenerated(generatedText);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generated Relevant Text</CardTitle>
      </CardHeader>
      <CardContent>
        <Textarea value={relevantText} readOnly className="h-32 mb-4" />
        <Button onClick={() => generateRelevantText(transcription, summary)}>Regenerate Relevant Text</Button>
      </CardContent>
    </Card>
  );
};

export default RelevantTextGenerator;