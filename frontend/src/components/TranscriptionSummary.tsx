import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';

interface TranscriptionSummaryProps {
  transcription: string;
  summary: string;
}

const TranscriptionSummary: React.FC<TranscriptionSummaryProps> = ({ transcription, summary }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Transcription and Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label htmlFor="transcription" className="block text-sm font-medium text-gray-700">Transcription</label>
          <Textarea id="transcription" value={transcription} readOnly className="h-24" />
        </div>
        <div>
          <label htmlFor="summary" className="block text-sm font-medium text-gray-700">Summary</label>
          <Textarea id="summary" value={summary} readOnly className="h-24" />
        </div>
      </CardContent>
    </Card>
  );
};

export default TranscriptionSummary;