import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface KeywordSuggestionsProps {
  keywords: string[];
}

const KeywordSuggestions: React.FC<KeywordSuggestionsProps> = ({ keywords }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Keyword Suggestions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {keywords.map((keyword, index) => (
            <Badge key={index} variant="secondary">{keyword}</Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default KeywordSuggestions;