import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

interface PlaylistAssignerProps {
  playlist: string;
}

const PlaylistAssigner: React.FC<PlaylistAssignerProps> = ({ playlist }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Assigned Playlist</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-lg font-semibold">{playlist}</p>
      </CardContent>
    </Card>
  );
};

export default PlaylistAssigner;