import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { coursesAPI, chatAPI } from '../services/api';
import { Send, ChevronRight, ChevronDown, ArrowLeft } from 'lucide-react';

export default function ChatInterface() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [selectedUnitId, setSelectedUnitId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const { data: courseStructure } = useQuery({
    queryKey: ['courseStructure', courseId],
    queryFn: async () => {
      const response = await coursesAPI.getCourseStructure(courseId);
      return response.data;
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: (data) => chatAPI.sendMessage(data),
    onSuccess: (response) => {
      setMessages(prev => [...prev, 
        { role: 'assistant', content: response.data.response }
      ]);
      if (!sessionId) {
        setSessionId(response.data.session_id);
      }
      setIsLoading(false);
    },
    onError: (error) => {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, 
        { role: 'assistant', content: 'Sorry, an error occurred. Please try again.' }
      ]);
      setIsLoading(false);
    },
  });

  const handleSend = () => {
    if (!message.trim() || isLoading) return;
    
    // Add user message immediately
    setMessages(prev => [...prev, { role: 'user', content: message }]);
    setIsLoading(true);
    
    const messageToSend = message;
    setMessage('');
    
    sendMessageMutation.mutate({
      message: messageToSend,
      session_id: sessionId,
      course_id: parseInt(courseId),
      current_unit_id: selectedUnitId,
    });
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="h-screen flex">
      {/* Sidebar */}
      <div className="w-80 bg-gray-50 border-r overflow-y-auto">
        <div className="p-4 border-b bg-white">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-2"
          >
            <ArrowLeft size={16} />
            Back to Dashboard
          </button>
          <h2 className="text-xl font-bold">{courseStructure?.course_name || 'Loading...'}</h2>
        </div>
        <div className="p-4">
          <h3 className="text-sm font-semibold text-gray-500 mb-2">UNITS</h3>
          <div className="space-y-1">
            {courseStructure?.units?.map(unit => (
              <UnitTree 
                key={unit.id} 
                unit={unit} 
                selectedUnitId={selectedUnitId}
                setSelectedUnitId={setSelectedUnitId}
              />
            ))}
            {(!courseStructure?.units || courseStructure.units.length === 0) && (
              <p className="text-sm text-gray-500">No units yet. Upload a PDF to get started.</p>
            )}
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-white">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-20">
              <p className="text-lg">Start a conversation!</p>
              <p className="text-sm mt-2">Ask questions about your course materials.</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl px-4 py-3 rounded-lg whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-800 px-4 py-3 rounded-lg">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t p-4 bg-gray-50">
          <div className="flex gap-2 max-w-4xl mx-auto">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your course..."
              className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !message.trim()}
              className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 flex items-center gap-2 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function UnitTree({ unit, selectedUnitId, setSelectedUnitId, level = 0 }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = unit.children && unit.children.length > 0;
  
  return (
    <div style={{ marginLeft: `${level * 12}px` }}>
      <div
        onClick={() => setSelectedUnitId(unit.id)}
        className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-gray-200 ${
          selectedUnitId === unit.id ? 'bg-blue-100 text-blue-700' : ''
        }`}
      >
        {hasChildren && (
          <button 
            onClick={(e) => { 
              e.stopPropagation(); 
              setIsExpanded(!isExpanded); 
            }}
            className="p-0.5 hover:bg-gray-300 rounded"
          >
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        )}
        {!hasChildren && <div className="w-5" />}
        <span className="text-sm truncate">{unit.name}</span>
      </div>
      {isExpanded && hasChildren && unit.children.map(child => (
        <UnitTree
          key={child.id}
          unit={child}
          selectedUnitId={selectedUnitId}
          setSelectedUnitId={setSelectedUnitId}
          level={level + 1}
        />
      ))}
    </div>
  );
}
