/**
 * Google OAuth callback page
 * Handles the authorization code from Google and exchanges it for JWT tokens
 */
'use client';

import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { exchangeCodeForTokens } from '@/lib/auth';
import { useAuthStore } from '@/store/auth';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth, setLoading, clearAuth } = useAuthStore();

  useEffect(() => {
    const handleCallback = async () => {
      setLoading(true);
      
      try {
        const code = searchParams.get('code');
        const error = searchParams.get('error');

        if (error) {
          console.error('OAuth error:', error);
          router.push('/?error=oauth_denied');
          return;
        }

        if (!code) {
          console.error('No authorization code received');
          router.push('/?error=oauth_invalid');
          return;
        }

        // Exchange code for tokens
        const authResponse = await exchangeCodeForTokens(code);
        
        // Store authentication data
        setAuth(
          {
            access_token: authResponse.access_token,
            refresh_token: authResponse.refresh_token,
          },
          authResponse.user
        );

        // Redirect to dashboard
        router.push('/dashboard');
        
      } catch (error) {
        console.error('Authentication failed:', error);
        clearAuth();
        router.push('/?error=auth_failed');
      } finally {
        setLoading(false);
      }
    };

    handleCallback();
  }, [searchParams, router, setAuth, setLoading, clearAuth]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/5 to-secondary/5">
      <div className="text-center">
        <div className="spinner mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-800">
          Completing your sign-in...
        </h2>
        <p className="text-gray-600 mt-2">
          Please wait while we set up your account
        </p>
      </div>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/5 to-secondary/5">
        <div className="text-center">
          <div className="spinner mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-800">
            Loading...
          </h2>
        </div>
      </div>
    }>
      <AuthCallbackContent />
    </Suspense>
  );
}