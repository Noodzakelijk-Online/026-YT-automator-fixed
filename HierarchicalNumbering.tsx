import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

interface HierarchicalNumberingProps {
  number: string;
}

const HierarchicalNumbering: React.FC<HierarchicalNumberingProps> = ({ number }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Hierarchical Number</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-lg font-semibold">{number}</p>
      </CardContent>
    </Card>
  );
};

export default HierarchicalNumbering;