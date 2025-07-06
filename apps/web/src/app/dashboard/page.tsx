/**
 * Dashboard page - protected route for authenticated users
 */
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { logout } from '@/lib/auth';

export default function Dashboard() {
  const router = useRouter();
  const { user, isAuthenticated, accessToken, clearAuth } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  const handleLogout = async () => {
    try {
      if (accessToken) {
        await logout(accessToken);
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuth();
      router.push('/');
    }
  };

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 to-secondary/5">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-display font-bold text-gray-800">
              Welcome back, {user.full_name?.split(' ')[0]}! 👋
            </h1>
            <p className="text-gray-600 mt-1">
              Ready for your wellness journey today?
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {user.avatar_url && (
              <img
                src={user.avatar_url}
                alt={user.full_name || 'User'}
                className="w-10 h-10 rounded-full"
              />
            )}
            <button
              onClick={handleLogout}
              className="btn bg-gray-100 text-gray-700 hover:bg-gray-200 px-4 py-2 rounded-lg"
            >
              Sign Out
            </button>
          </div>
        </header>

        {/* User Info Card */}
        <div className="card max-w-2xl mx-auto">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Your Profile
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Email:</span>
              <span className="font-medium">{user.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Company:</span>
              <span className="font-medium">{user.company_domain || 'Not specified'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Timezone:</span>
              <span className="font-medium">{user.timezone || 'UTC'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Preferred Break Duration:</span>
              <span className="font-medium">{user.preferred_break_duration || 10} minutes</span>
            </div>
            {user.biggest_challenge && (
              <div className="flex justify-between">
                <span className="text-gray-600">Biggest Challenge:</span>
                <span className="font-medium capitalize">{user.biggest_challenge}</span>
              </div>
            )}
          </div>
        </div>

        {/* Welcome Message */}
        <div className="text-center mt-8">
          <div className="inline-flex items-center gap-2 bg-green-100 text-green-800 px-4 py-2 rounded-full">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Authentication Complete!
          </div>
          <p className="text-gray-600 mt-4">
            🎉 Your takeabreak.life account is set up and ready.
            <br />
            The wellness features are being built - stay tuned!
          </p>
        </div>
      </div>
    </div>
  );
}