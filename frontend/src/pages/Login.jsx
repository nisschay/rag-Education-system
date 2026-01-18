import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '@/services/api';
import { useAuth } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { GraduationCap, BookOpen, Brain, Sparkles, Mail, Lock, User, Eye, EyeOff, Loader2 } from 'lucide-react';

// Google OAuth Client ID - set this in your environment
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

export default function Login() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [googleLoaded, setGoogleLoaded] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  // Load Google Sign-In script
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;
    
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setGoogleLoaded(true);
    document.body.appendChild(script);
    
    return () => {
      document.body.removeChild(script);
    };
  }, []);

  // Initialize Google Sign-In button
  useEffect(() => {
    if (!googleLoaded || !GOOGLE_CLIENT_ID || !window.google) return;
    
    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: handleGoogleCallback,
    });
    
    window.google.accounts.id.renderButton(
      document.getElementById('google-signin-btn'),
      { 
        theme: 'filled_black', 
        size: 'large', 
        width: '100%',
        text: isSignUp ? 'signup_with' : 'signin_with',
        shape: 'rectangular',
      }
    );
  }, [googleLoaded, isSignUp]);

  const handleGoogleCallback = async (response) => {
    setIsLoading(true);
    setError('');
    
    try {
      const result = await authAPI.googleAuth(response.credential);
      login(result.data);
      navigate('/dashboard');
    } catch (error) {
      console.error('Google auth failed:', error);
      setError('Google sign-in failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (isSignUp && password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    
    setIsLoading(true);
    
    try {
      let response;
      if (isSignUp) {
        response = await authAPI.register(email, password, name);
      } else {
        response = await authAPI.login(email, password, name);
      }
      login(response.data);
      navigate('/dashboard');
    } catch (error) {
      console.error('Auth failed:', error);
      const message = error.response?.data?.detail || 'Authentication failed. Please try again.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white p-12 flex-col justify-between relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-300 rounded-full blur-3xl"></div>
        </div>
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-12">
            <div className="p-2 bg-white/20 rounded-xl backdrop-blur-sm">
              <GraduationCap className="h-8 w-8" />
            </div>
            <span className="text-2xl font-bold">RAG Education</span>
          </div>
          <h1 className="text-5xl font-bold mb-6 leading-tight">
            Learn Smarter with<br />
            <span className="text-blue-200">AI-Powered</span> Education
          </h1>
          <p className="text-xl text-blue-100 max-w-md">
            Upload your study materials and chat with an intelligent tutor that understands your content.
          </p>
        </div>
        
        <div className="space-y-6 relative z-10">
          <div className="flex items-start gap-4 p-4 bg-white/10 rounded-xl backdrop-blur-sm">
            <div className="p-3 bg-white/20 rounded-lg">
              <BookOpen className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Upload Any PDF</h3>
              <p className="text-sm text-blue-100">Textbooks, notes, research papers - we handle it all</p>
            </div>
          </div>
          <div className="flex items-start gap-4 p-4 bg-white/10 rounded-xl backdrop-blur-sm">
            <div className="p-3 bg-white/20 rounded-lg">
              <Brain className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">AI-Powered Learning</h3>
              <p className="text-sm text-blue-100">Get instant explanations, summaries, and answers</p>
            </div>
          </div>
          <div className="flex items-start gap-4 p-4 bg-white/10 rounded-xl backdrop-blur-sm">
            <div className="p-3 bg-white/20 rounded-lg">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Personalized Experience</h3>
              <p className="text-sm text-blue-100">Learn at your own pace with adaptive tutoring</p>
            </div>
          </div>
        </div>
        
        <p className="text-sm text-blue-200 relative z-10">
          Powered by Gemini 2.5 Flash & RAG Technology
        </p>
      </div>
      
      {/* Right side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex justify-center mb-8 lg:hidden">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-600 rounded-xl">
                <GraduationCap className="h-8 w-8 text-white" />
              </div>
              <span className="text-2xl font-bold">RAG Education</span>
            </div>
          </div>
          
          <Card className="border-0 shadow-xl">
            <CardHeader className="text-center pb-2">
              <CardTitle className="text-3xl font-bold">
                {isSignUp ? 'Create Account' : 'Welcome Back'}
              </CardTitle>
              <CardDescription className="text-base">
                {isSignUp 
                  ? 'Start your AI-powered learning journey' 
                  : 'Sign in to continue your learning journey'}
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {/* Google Sign-In Button */}
              {GOOGLE_CLIENT_ID && (
                <>
                  <div id="google-signin-btn" className="w-full flex justify-center mb-4"></div>
                  
                  <div className="relative my-6">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-border"></div>
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-card px-2 text-muted-foreground">Or continue with email</span>
                    </div>
                  </div>
                </>
              )}
              
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-lg border border-destructive/20">
                    {error}
                  </div>
                )}
                
                {isSignUp && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Full Name</label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        type="text"
                        placeholder="John Doe"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="pl-10 h-11"
                        required={isSignUp}
                      />
                    </div>
                  </div>
                )}
                
                <div className="space-y-2">
                  <label className="text-sm font-medium">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-10 h-11"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-10 pr-10 h-11"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
                
                {isSignUp && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Confirm Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        type={showPassword ? 'text' : 'password'}
                        placeholder="••••••••"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="pl-10 h-11"
                        required={isSignUp}
                      />
                    </div>
                  </div>
                )}
                
                {!isSignUp && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Name (optional for new users)</label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        type="text"
                        placeholder="Your name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="pl-10 h-11"
                      />
                    </div>
                  </div>
                )}
                
                <Button type="submit" className="w-full h-11 text-base font-semibold" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      {isSignUp ? 'Creating account...' : 'Signing in...'}
                    </>
                  ) : (
                    isSignUp ? 'Create Account' : 'Sign In'
                  )}
                </Button>
              </form>
              
              <div className="mt-6 text-center">
                <p className="text-sm text-muted-foreground">
                  {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setIsSignUp(!isSignUp);
                      setError('');
                      setPassword('');
                      setConfirmPassword('');
                    }}
                    className="text-primary font-semibold hover:underline"
                  >
                    {isSignUp ? 'Sign in' : 'Sign up'}
                  </button>
                </p>
              </div>
              
              {!isSignUp && (
                <p className="text-center text-xs text-muted-foreground mt-4">
                  New users will be registered automatically with their email and password.
                </p>
              )}
            </CardContent>
          </Card>
          
          <p className="text-center text-xs text-muted-foreground mt-6">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </div>
    </div>
  );
}
