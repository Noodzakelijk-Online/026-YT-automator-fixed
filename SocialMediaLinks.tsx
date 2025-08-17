import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const SocialMediaLinks: React.FC = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Social Media Links</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="twitter">Twitter</Label>
          <Input id="twitter" placeholder="https://twitter.com/yourusername" />
        </div>
        <div>
          <Label htmlFor="instagram">Instagram</Label>
          <Input id="instagram" placeholder="https://instagram.com/yourusername" />
        </div>
        <div>
          <Label htmlFor="facebook">Facebook</Label>
          <Input id="facebook" placeholder="https://facebook.com/yourusername" />
        </div>
      </CardContent>
    </Card>
  );
};

export default SocialMediaLinks;