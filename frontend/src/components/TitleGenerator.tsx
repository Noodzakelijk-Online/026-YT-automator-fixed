import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

interface TitleGeneratorProps {
  title: string;
}

const TitleGenerator: React.FC<TitleGeneratorProps> = ({ title }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Generated Title</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-lg font-semibold">{title}</p>
      </CardContent>
    </Card>
  );
};

export default TitleGenerator;