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
import './App.css';

// The address of your FastAPI backend
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

const samplePrompts = [
  'Visualize Pythagoras theorem using squares on a triangle.',
  'Animate binary search on a sorted array with pointers.',
  'Show a queue enqueue/dequeue process with labels.',
];

const MODEL_NAME = 'Qwen3-32B';

function App() {
  const [prompt, setPrompt] = useState<string>('');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('idle');
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState<number>(0);

  const isProcessing = status === 'submitting' || status === 'PENDING' || status === 'PROCESSING';
  const statusLabel = status === 'submitting' ? 'Submitting' : status;

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
      <CssBaseline />
      <div className="page">
        <div className="bg-orb orb-1" />
        <div className="bg-orb orb-2" />
        <div className="bg-grid" />
        <Container maxWidth="lg" className="shell">
          <header className="topbar">
            <div className="brand">
              <span className="brand-dot" />
              <span>Playground</span>
            </div>
            <div className="pill">Prototype</div>
          </header>

          <div className="layout">
            <section className="hero">
              <Typography variant="h2" component="h1" className="headline" gutterBottom>
                Text-to-Manim, in minutes.
              </Typography>
              <Typography variant="h6" className="subhead" gutterBottom>
                Turn algorithms and math concepts into crisp animations. Describe what you want and
                get a rendered video back.
              </Typography>
              <div className="stat-row">
                <div className="stat-card">
                  <span className="stat-label">LLM</span>
                  <span className="stat-value">{MODEL_NAME}</span>
                </div>
                <div className="stat-card">
                  <span className="stat-label">Renderer</span>
                  <span className="stat-value">Manim CE</span>
                </div>
                <div className="stat-card">
                  <span className="stat-label">Backend</span>
                  <span className="stat-value">FastAPI</span>
                </div>
              </div>
            </section>

            <section className="panel">
              <Typography variant="h6" className="panel-title">
                Describe your animation
              </Typography>
              <Typography className="panel-subtitle">
                Keep it clear and visual. The model handles the rest.
              </Typography>

              <Box component="form" onSubmit={handleSubmit} className="panel-form">
                <TextField
                  fullWidth
                  multiline
                  rows={5}
                  variant="outlined"
                  label="Animation Prompt"
                  placeholder="A blue circle transforms into a red square, then fades out."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  disabled={isProcessing}
                />
                <div className="actions">
                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    disabled={isProcessing}
                    className="primary"
                  >
                    {isProcessing ? <CircularProgress size={22} color="inherit" /> : 'Generate Animation'}
                  </Button>
                  <Button
                    type="button"
                    variant="text"
                    disabled={isProcessing || !prompt}
                    onClick={() => setPrompt('')}
                    className="ghost"
                  >
                    Clear
                  </Button>
                </div>
              </Box>

              <div className="sample-row">
                <Typography className="sample-label">Try one:</Typography>
                <div className="sample-buttons">
                  {samplePrompts.map((text) => (
                    <button
                      key={text}
                      type="button"
                      className="sample-button"
                      onClick={() => setPrompt(text)}
                      disabled={isProcessing}
                    >
                      {text}
                    </button>
                  ))}
                </div>
              </div>

              {isProcessing && (
                <Box className="status-card">
                  <div className="status-header">
                    <Typography variant="h6">Status: {statusLabel}</Typography>
                    <Typography className="status-time">{elapsedTime}s</Typography>
                  </div>
                  <div className="status-body">
                    <CircularProgress />
                    <Typography className="status-text">
                      Rendering your animation. This can take a moment.
                    </Typography>
                  </div>
                </Box>
              )}

              {error && (
                <Alert severity="error" className="error-card">
                  <Typography gutterBottom>An error occurred</Typography>
                  <pre className="error-body">{error}</pre>
                </Alert>
              )}

              {videoUrl && (
                <Box className="video-card">
                  <Typography variant="h6" gutterBottom>
                    Animation Ready
                  </Typography>
                  <video controls src={videoUrl} autoPlay loop />
                </Box>
              )}
            </section>
          </div>

          <footer className="footer">
            Built as a side-project prototype • Model: {MODEL_NAME} • Provider: Groq •{' '}
            <a href="https://github.com/Aneesh-382005/Playground" target="_blank" rel="noreferrer">
              GitHub
            </a>
          </footer>
        </Container>
      </div>
    </>
  );
}

export default App;