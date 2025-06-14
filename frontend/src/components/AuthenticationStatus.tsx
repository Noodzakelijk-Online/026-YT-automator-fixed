import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, AlertCircle, Youtube } from 'lucide-react';

interface AuthenticationStatusProps {
  isAuthenticated: boolean;
  onAuthenticate: () => void;
}

const AuthenticationStatus: React.FC<AuthenticationStatusProps> = ({
  isAuthenticated,
  onAuthenticate
}) => {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Youtube className="h-6 w-6 text-red-600" />
          <div>
            <h3 className="text-lg font-semibold">YouTube Authentication</h3>
            <p className="text-sm text-gray-600">
              {isAuthenticated 
                ? 'Connected to your YouTube account' 
                : 'Connect your YouTube account to upload videos'
              }
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          {isAuthenticated ? (
            <Alert className="border-green-500 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                Authenticated
              </AlertDescription>
            </Alert>
          ) : (
            <>
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Not authenticated
                </AlertDescription>
              </Alert>
              <Button onClick={onAuthenticate} variant="outline">
                Connect YouTube
              </Button>
            </>
          )}
        </div>
      </div>
      
      {!isAuthenticated && (
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> You need to authenticate with your Google account to upload videos to YouTube. 
            This will open a new window for secure authentication.
          </p>
        </div>
      )}
    </Card>
  );
};

export default AuthenticationStatus;

