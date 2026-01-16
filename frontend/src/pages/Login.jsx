import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '@/services/api';
import { useAuth } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { GraduationCap, BookOpen, Brain, Sparkles } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      const response = await authAPI.login(email, name);
      login(response.data);
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
      setError('Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary to-primary/80 text-primary-foreground p-12 flex-col justify-between">
        <div>
          <div className="flex items-center gap-3 mb-8">
            <GraduationCap className="h-10 w-10" />
            <span className="text-2xl font-bold">RAG Education</span>
          </div>
          <h1 className="text-4xl font-bold mb-4">
            Learn Smarter with AI-Powered Education
          </h1>
          <p className="text-lg opacity-90">
            Upload your study materials and chat with an intelligent tutor that understands your content.
          </p>
        </div>
        
        <div className="space-y-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-white/10 rounded-lg">
              <BookOpen className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Upload Any PDF</h3>
              <p className="text-sm opacity-80">Upload textbooks, notes, or research papers</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="p-3 bg-white/10 rounded-lg">
              <Brain className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">AI-Powered Learning</h3>
              <p className="text-sm opacity-80">Get explanations, summaries, and answers</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="p-3 bg-white/10 rounded-lg">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Personalized Experience</h3>
              <p className="text-sm opacity-80">Learn at your own pace with adaptive tutoring</p>
            </div>
          </div>
        </div>
        
        <p className="text-sm opacity-70">
          Powered by Gemini 2.5 Flash & RAG Technology
        </p>
      </div>
      
      {/* Right side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4 lg:hidden">
              <div className="p-3 bg-primary rounded-xl">
                <GraduationCap className="h-8 w-8 text-primary-foreground" />
              </div>
            </div>
            <CardTitle className="text-2xl">Welcome Back</CardTitle>
            <CardDescription>
              Sign in to continue your learning journey
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              {error && (
                <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                  {error}
                </div>
              )}
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Email</label>
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Name (optional)</label>
                <Input
                  type="text"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>
            
            <p className="text-center text-sm text-muted-foreground mt-6">
              New user? Just enter your email to get started.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
