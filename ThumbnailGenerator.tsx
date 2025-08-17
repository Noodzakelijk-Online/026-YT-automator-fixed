import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ThumbnailGeneratorProps {
  thumbnailUrl: string;
}

const ThumbnailGenerator: React.FC<ThumbnailGeneratorProps> = ({ thumbnailUrl }) => {
  const [currentThumbnail, setCurrentThumbnail] = useState(thumbnailUrl);

  const generateNewThumbnail = () => {
    // In a real implementation, this would call a service to generate a new thumbnail
    console.log('Generating new thumbnail...');
    // For demonstration, we're just cycling through a few placeholder images
    const placeholders = [
      'https://via.placeholder.com/1280x720.png?text=Thumbnail+1',
      'https://via.placeholder.com/1280x720.png?text=Thumbnail+2',
      'https://via.placeholder.com/1280x720.png?text=Thumbnail+3',
    ];
    const nextIndex = (placeholders.indexOf(currentThumbnail) + 1) % placeholders.length;
    setCurrentThumbnail(placeholders[nextIndex]);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generated Thumbnail</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <img src={currentThumbnail} alt="Generated Thumbnail" className="w-full h-auto mx-auto object-cover rounded-lg" />
        <Button onClick={generateNewThumbnail}>Generate New Thumbnail</Button>
      </CardContent>
    </Card>
  );
};

export default ThumbnailGenerator;