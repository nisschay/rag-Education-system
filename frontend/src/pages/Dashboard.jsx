import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { coursesAPI } from '../services/api';
import { Plus, Upload, MessageSquare } from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateCourse, setShowCreateCourse] = useState(false);
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
      setShowCreateCourse(false);
      setCourseName('');
      setCourseDescription('');
    },
  });

  const handleCreateCourse = () => {
    createCourseMutation.mutate({
      name: courseName,
      description: courseDescription,
    });
  };

  if (isLoading) return <div className="flex items-center justify-center h-screen">Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">My Courses</h1>
          <button
            onClick={() => setShowCreateCourse(true)}
            className="flex items-center gap-2 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            <Plus size={20} />
            New Course
          </button>
        </div>

        {showCreateCourse && (
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h2 className="text-xl font-bold mb-4">Create New Course</h2>
            <input
              type="text"
              placeholder="Course Name"
              value={courseName}
              onChange={(e) => setCourseName(e.target.value)}
              className="w-full px-3 py-2 border rounded mb-3"
            />
            <textarea
              placeholder="Description"
              value={courseDescription}
              onChange={(e) => setCourseDescription(e.target.value)}
              className="w-full px-3 py-2 border rounded mb-3"
              rows="3"
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreateCourse}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                Create
              </button>
              <button
                onClick={() => setShowCreateCourse(false)}
                className="bg-gray-300 px-4 py-2 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses?.map((course) => (
            <CourseCard key={course.id} course={course} navigate={navigate} />
          ))}
        </div>
      </div>
    </div>
  );
}

function CourseCard({ course, navigate }) {
  const [showUpload, setShowUpload] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: () => coursesAPI.uploadDocument(course.id, file),
    onSuccess: () => {
      alert('Document uploaded successfully!');
      setShowUpload(false);
      setFile(null);
      queryClient.invalidateQueries(['courses']);
    },
    onError: (error) => {
      alert('Upload failed: ' + error.message);
    },
  });

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      await uploadMutation.mutateAsync();
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
      <h3 className="text-xl font-bold mb-2">{course.name}</h3>
      <p className="text-gray-600 text-sm mb-4">{course.description || 'No description'}</p>
      
      <div className="flex gap-2">
        <button
          onClick={() => navigate(`/chat/${course.id}`)}
          className="flex items-center gap-1 bg-blue-500 text-white px-3 py-2 rounded text-sm hover:bg-blue-600"
        >
          <MessageSquare size={16} />
          Chat
        </button>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="flex items-center gap-1 bg-green-500 text-white px-3 py-2 rounded text-sm hover:bg-green-600"
        >
          <Upload size={16} />
          Upload
        </button>
      </div>

      {showUpload && (
        <div className="mt-4 pt-4 border-t">
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="mb-2 text-sm w-full"
          />
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="w-full bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 disabled:bg-gray-300"
          >
            {uploading ? 'Uploading...' : 'Upload PDF'}
          </button>
        </div>
      )}
    </div>
  );
}
