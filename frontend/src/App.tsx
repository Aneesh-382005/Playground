import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  TextField,
  Button,
  Box,
  CircularProgress,
  Alert,
  CssBaseline,
} from '@mui/material';

// The address of your FastAPI backend
const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [prompt, setPrompt] = useState<string>('');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('idle');
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState<number>(0);

  const isProcessing = status === 'submitting' || status === 'PENDING' || status === 'PROCESSING';

  // Polling logic to check the status of a job
  useEffect(() => {
    let intervalId: number | undefined;

    if (taskId && (status === 'PENDING' || status === 'PROCESSING')) {
      // Start a timer
      setElapsedTime(0);
      intervalId = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);

      const checkStatus = async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/status/${taskId}`);
          if (!response.ok) throw new Error('Status check failed');
          const data = await response.json();

          setStatus(data.status);

          if (data.status === 'SUCCESS') {
            // We use the video path from the API to build a full URL
            setVideoUrl(`${API_BASE_URL}/${data.result}`);
            setTaskId(null); // Stop polling
          } else if (data.status === 'FAILURE') {
            setError(data.error);
            setTaskId(null); // Stop polling
          } else {
            // If still pending/processing, check again after 3 seconds
            setTimeout(checkStatus, 3000);
          }
        } catch (err) {
          setError('Failed to fetch status.');
          setTaskId(null); // Stop polling
        }
      };
      // Start the first status check
      setTimeout(checkStatus, 1000);
    }

    // Cleanup function to stop the timer when the component unmounts or the job finishes
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [taskId, status]);


  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!prompt.trim()) return;
    setError(null);
    setVideoUrl(null);
    setStatus('submitting');

    try {
      const response = await fetch(`${API_BASE_URL}/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      if (!response.ok) throw new Error((await response.json()).detail || 'Failed to submit job');
      const data = await response.json();
      setTaskId(data.taskID);
      setStatus('PENDING');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred.');
      setStatus('idle');
    }
  };

  return (
    <>
      <CssBaseline /> {/* Ensures a consistent baseline style */}
      <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%', paddingTop: '4rem' }}>
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
        <Typography variant="h2" component="h1" gutterBottom>
          Playground: Text-to-Manim
        </Typography>
        <Typography variant="h6" color="textSecondary" gutterBottom>
          Describe an animation, and bring it to life.
        </Typography>

        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 4 }}>
          <TextField
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            label="Animation Prompt"
            placeholder="A blue circle transforming into a red square, with both fading in and out."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isProcessing}
          />
          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={isProcessing}
            sx={{ mt: 2 }}
          >
            {isProcessing ? <CircularProgress size={24} color="inherit" /> : 'Generate Animation'}
          </Button>
        </Box>

        {isProcessing && (
           <Box sx={{ mt: 4 }}>
             <Typography variant="h6">Status: {status}</Typography>
             <Typography color="textSecondary">Time Elapsed: {elapsedTime}s</Typography>
             <CircularProgress sx={{ mt: 2 }} />
             <Typography color="textSecondary" sx={{mt: 1}}>Your video is being generated. Please wait...</Typography>
           </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mt: 4, textAlign: 'left' }}>
            <Typography gutterBottom>An Error Occurred</Typography>
            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{error}</pre>
          </Alert>
        )}

        {videoUrl && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h5" gutterBottom>Animation Ready!</Typography>
            <video
              controls
              style={{ maxWidth: '100%', borderRadius: '8px', marginTop: '1rem' }}
              src={videoUrl}
              autoPlay
              loop
            >
              Your browser does not support the video tag.
            </video>
          </Box>
        )}
        </Container>
      </Box>
    </>
  );
}

export default App;