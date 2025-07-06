'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import LoginButton from '@/components/LoginButton';

export default function Home() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuthStore();

  // Check for error parameters
  const error = searchParams.get('error');

  useEffect(() => {
    // Redirect to dashboard if already authenticated
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  const getErrorMessage = (errorCode: string | null) => {
    switch (errorCode) {
      case 'oauth_denied':
        return 'Sign-in was cancelled. Please try again.';
      case 'oauth_invalid':
        return 'Invalid authorization. Please try signing in again.';
      case 'auth_failed':
        return 'Authentication failed. Please try again.';
      default:
        return null;
    }
  };

  const errorMessage = getErrorMessage(error);

  return (
    <main className="min-h-screen bg-gradient-to-br from-primary/5 to-secondary/5">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Header */}
          <h1 className="text-5xl md:text-6xl font-display font-bold mb-6">
            Welcome to{' '}
            <span className="text-gradient">takeabreak.life</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Your intelligent wellness partner that integrates with your calendar 
            to deliver personalized break recommendations, helping you prevent burnout 
            and boost productivity.
          </p>

          {/* Error Message */}
          {errorMessage && (
            <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 max-w-md mx-auto">
              {errorMessage}
            </div>
          )}

          {/* Login Section */}
          <div className="mb-12">
            <LoginButton />
            <p className="text-sm text-gray-500 mt-4">
              Sign in with your work Google account to get started
            </p>
          </div>

          {/* Features Preview */}
          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Calendar Integration
              </h3>
              <p className="text-gray-600">
                Seamlessly connects with your work calendar to find perfect break opportunities
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                AI-Powered Recommendations
              </h3>
              <p className="text-gray-600">
                Intelligent suggestions based on your schedule, stress levels, and preferences
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Boost Productivity
              </h3>
              <p className="text-gray-600">
                Strategic breaks that actually improve your focus and prevent burnout
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}