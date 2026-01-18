import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { coursesAPI } from '@/services/api';
import { useAuth } from '@/App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { 
  Plus, 
  Upload, 
  MessageSquare, 
  Trash2, 
  FileText, 
  GraduationCap,
  LogOut,
  MoreVertical,
  Book,
  Clock
} from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, logout } = useAuth();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [courseName, setCourseName] = useState('');
  const [courseDescription, setCourseDescription] = useState('');

  const { data: courses, isLoading } = useQuery({
    queryKey: ['courses'],
    queryFn: async () => {
      const response = await coursesAPI.getCourses();
      return response.data;
    },
  });

  const createCourseMutation = useMutation({
    mutationFn: (data) => coursesAPI.createCourse(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['courses']);
      setIsCreateOpen(false);
      setCourseName('');
      setCourseDescription('');
    },
  });

  const handleCreateCourse = () => {
    if (!courseName.trim()) return;
    createCourseMutation.mutate({
      name: courseName,
      description: courseDescription,
    });
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary rounded-lg">
                <GraduationCap className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold">RAG Education</h1>
                <p className="text-sm text-muted-foreground">Your AI Study Companion</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                Welcome, <span className="font-medium text-foreground">{user?.name || user?.email}</span>
              </span>
              <Button variant="ghost" size="icon" onClick={handleLogout}>
                <LogOut className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold">My Courses</h2>
            <p className="text-muted-foreground mt-1">
              Manage your courses and study materials
            </p>
          </div>
          
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Course
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Course</DialogTitle>
                <DialogDescription>
                  Add a new course to start uploading study materials.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Course Name</label>
                  <Input
                    placeholder="e.g., Machine Learning 101"
                    value={courseName}
                    onChange={(e) => setCourseName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Description</label>
                  <Textarea
                    placeholder="What is this course about?"
                    value={courseDescription}
                    onChange={(e) => setCourseDescription(e.target.value)}
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateCourse} disabled={createCourseMutation.isPending}>
                  {createCourseMutation.isPending ? 'Creating...' : 'Create Course'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : courses?.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <Book className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No courses yet</h3>
              <p className="text-muted-foreground text-center mb-4">
                Create your first course to start uploading study materials.
              </p>
              <Button onClick={() => setIsCreateOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Course
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses?.map((course) => (
              <CourseCard key={course.id} course={course} navigate={navigate} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function CourseCard({ course, navigate }) {
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isDocsOpen, setIsDocsOpen] = useState(false);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const queryClient = useQueryClient();

  const { data: documents } = useQuery({
    queryKey: ['documents', course.id],
    queryFn: async () => {
      const response = await coursesAPI.getCourseDocuments(course.id);
      return response.data;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: () => coursesAPI.uploadDocuments(course.id, files),
    onSuccess: () => {
      queryClient.invalidateQueries(['documents', course.id]);
      setIsUploadOpen(false);
      setFiles([]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => coursesAPI.deleteCourse(course.id),
    onSuccess: () => {
      queryClient.invalidateQueries(['courses']);
    },
  });

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    try {
      await uploadMutation.mutateAsync();
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const docCount = documents?.documents?.length || 0;

  return (
    <Card className="group hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{course.name}</CardTitle>
            <CardDescription className="mt-1 line-clamp-2">
              {course.description || 'No description'}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <FileText className="h-4 w-4" />
            <span>{docCount} document{docCount !== 1 ? 's' : ''}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            <span>{new Date(course.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </CardContent>
      
      <CardFooter className="flex gap-2 flex-wrap">
        <Button size="sm" onClick={() => navigate(`/chat/${course.id}`)}>
          <MessageSquare className="h-4 w-4 mr-1" />
          Chat
        </Button>
        
        <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
          <DialogTrigger asChild>
            <Button size="sm" variant="secondary">
              <Upload className="h-4 w-4 mr-1" />
              Upload
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Upload Documents</DialogTitle>
              <DialogDescription>
                Upload PDF files to add to this course (max 10 files, 10MB each).
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Input
                type="file"
                accept=".pdf"
                multiple
                onChange={handleFileChange}
              />
              {files.length > 0 && (
                <div className="mt-3 space-y-1">
                  <p className="text-sm font-medium">Selected files:</p>
                  {files.map((f, idx) => (
                    <p key={idx} className="text-sm text-muted-foreground">
                      • {f.name} ({formatFileSize(f.size)})
                    </p>
                  ))}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { setIsUploadOpen(false); setFiles([]); }}>
                Cancel
              </Button>
              <Button onClick={handleUpload} disabled={files.length === 0 || uploading}>
                {uploading ? 'Uploading...' : `Upload ${files.length} file${files.length !== 1 ? 's' : ''}`}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={isDocsOpen} onOpenChange={setIsDocsOpen}>
          <DialogTrigger asChild>
            <Button size="sm" variant="outline">
              <FileText className="h-4 w-4 mr-1" />
              Docs
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Documents</DialogTitle>
              <DialogDescription>
                Uploaded documents for {course.name}
              </DialogDescription>
            </DialogHeader>
            <div className="py-4 max-h-80 overflow-auto">
              {docCount === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No documents uploaded yet.
                </p>
              ) : (
                <div className="space-y-2">
                  {documents?.documents?.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium text-sm">{doc.filename}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatFileSize(doc.file_size)} • {doc.chunks_count} chunks
                          </p>
                        </div>
                      </div>
                      <Badge variant="secondary">{formatFileSize(doc.file_size)}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
        
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button size="sm" variant="ghost" className="text-destructive hover:text-destructive">
              <Trash2 className="h-4 w-4" />
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Course</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete "{course.name}"? This will permanently delete
                all documents, chat history, and data associated with this course.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                onClick={() => deleteMutation.mutate()}
              >
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </CardFooter>
    </Card>
  );
}
