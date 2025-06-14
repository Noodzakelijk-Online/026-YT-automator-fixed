import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';

interface MetadataGeneratorProps {
  metadata: {
    title: string;
    description: string;
    tags: string[];
    category: string;
    privacyStatus: string;
    license: string;
    embeddable: boolean;
    publicStatsViewable: boolean;
  };
  onMetadataChange: (newMetadata: any) => void;
}

const MetadataGenerator: React.FC<MetadataGeneratorProps> = ({ metadata, onMetadataChange }) => {
  const [localMetadata, setLocalMetadata] = useState(metadata);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setLocalMetadata(prev => ({ ...prev, [name]: value }));
  };

  const handleSwitchChange = (name: string) => {
    setLocalMetadata(prev => ({ ...prev, [name]: !prev[name] }));
  };

  const handleTagsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const tags = e.target.value.split(',').map(tag => tag.trim());
    setLocalMetadata(prev => ({ ...prev, tags }));
  };

  const regenerateMetadata = async () => {
    // Simulating AI-generated metadata
    const aiGeneratedMetadata = {
      title: "AI-Generated: Exciting New Features in Web Development 2024",
      description: "Explore the latest trends and innovations in web development for 2024. This video covers new JavaScript APIs, CSS improvements, and performance optimizations that will revolutionize how we build websites.",
      tags: ['web development', '2024 trends', 'JavaScript', 'CSS', 'performance'],
      category: "Science & Technology",
      privacyStatus: "public",
      license: "youtube",
      embeddable: true,
      publicStatsViewable: true,
    };
    setLocalMetadata(aiGeneratedMetadata);
    onMetadataChange(aiGeneratedMetadata);
  };

  const saveMetadata = () => {
    onMetadataChange(localMetadata);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI-Generated Metadata</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="title">Title</Label>
          <Input id="title" name="title" value={localMetadata.title} onChange={handleInputChange} />
        </div>
        <div>
          <Label htmlFor="description">Description</Label>
          <Textarea id="description" name="description" value={localMetadata.description} onChange={handleInputChange} className="h-24" />
        </div>
        <div>
          <Label htmlFor="tags">Tags (comma-separated)</Label>
          <Input id="tags" name="tags" value={localMetadata.tags.join(', ')} onChange={handleTagsChange} />
        </div>
        <div>
          <Label htmlFor="category">Category</Label>
          <Input id="category" name="category" value={localMetadata.category} onChange={handleInputChange} />
        </div>
        <div>
          <Label htmlFor="privacyStatus">Privacy Status</Label>
          <Input id="privacyStatus" name="privacyStatus" value={localMetadata.privacyStatus} onChange={handleInputChange} />
        </div>
        <div>
          <Label htmlFor="license">License</Label>
          <Input id="license" name="license" value={localMetadata.license} onChange={handleInputChange} />
        </div>
        <div className="flex items-center space-x-2">
          <Switch id="embeddable" checked={localMetadata.embeddable} onCheckedChange={() => handleSwitchChange('embeddable')} />
          <Label htmlFor="embeddable">Embeddable</Label>
        </div>
        <div className="flex items-center space-x-2">
          <Switch id="publicStatsViewable" checked={localMetadata.publicStatsViewable} onCheckedChange={() => handleSwitchChange('publicStatsViewable')} />
          <Label htmlFor="publicStatsViewable">Public Stats Viewable</Label>
        </div>
        <div className="flex space-x-2">
          <Button onClick={regenerateMetadata}>Regenerate Metadata</Button>
          <Button onClick={saveMetadata}>Save Metadata</Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default MetadataGenerator;