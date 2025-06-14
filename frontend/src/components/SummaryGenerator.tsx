import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';

interface SummaryGeneratorProps {
  transcription: string;
  onSummaryGenerated: (summary: string) => void;
}

const SummaryGenerator: React.FC<SummaryGeneratorProps> = ({ transcription, onSummaryGenerated }) => {
  const [summary, setSummary] = useState<string>('');

  useEffect(() => {
    if (transcription) {
      generateSummary(transcription);
    }
  }, [transcription]);

  const generateSummary = async (text: string) => {
    // Simulating summary generation
    await new Promise(resolve => setTimeout(resolve, 1000));
    const generatedSummary = `This video provides an overview of upcoming web development trends for 2024, focusing on new JavaScript APIs, CSS enhancements, and performance optimization techniques. Key topics include interactive web applications, responsive design improvements, and strategies for faster load times.`;
    setSummary(generatedSummary);
    onSummaryGenerated(generatedSummary);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Video Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <Textarea value={summary} readOnly className="h-24 mb-4" />
        <Button onClick={() => generateSummary(transcription)}>Regenerate Summary</Button>
      </CardContent>
    </Card>
  );
};

export default SummaryGenerator;