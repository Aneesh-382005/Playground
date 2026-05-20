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

const PROVIDER_OPTIONS = [
  { id: 'groq', label: 'Groq', model: 'qwen/qwen3-32b' },
  { id: 'nvidia', label: 'NVIDIA', model: 'google/gemma-2-2b-it' },
] as const;

type ProviderId = (typeof PROVIDER_OPTIONS)[number]['id'];

function App() {
  const [prompt, setPrompt] = useState<string>('');
  const [provider, setProvider] = useState<ProviderId>('groq');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('idle');
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState<number>(0);

  const providerConfig = provider === 'nvidia' ? PROVIDER_OPTIONS[1] : PROVIDER_OPTIONS[0];

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
        body: JSON.stringify({ prompt, provider }),
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

          <Box mt={2} mb={2}>
            <Alert severity="info">
              Desktop app coming soon! - a native desktop client is on the way.
            </Alert>
          </Box>

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
                  <span className="stat-label">Provider</span>
                  <span className="stat-value">{providerConfig.label}</span>
                </div>
                <div className="stat-card">
                  <span className="stat-label">Model</span>
                  <span className="stat-value">{providerConfig.model}</span>
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
                Groq is the default. Switch providers only if you want to experiment.
              </Typography>

              <Box component="form" onSubmit={handleSubmit} className="panel-form">
                <div className="provider-row">
                  <span className="provider-label">Provider</span>
                  <div className="provider-switch" role="group" aria-label="LLM provider">
                    {PROVIDER_OPTIONS.map((option) => (
                      <button
                        key={option.id}
                        type="button"
                        className={`provider-button ${provider === option.id ? 'active' : ''}`}
                        onClick={() => setProvider(option.id)}
                        disabled={isProcessing}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                  <span className="provider-hint">{providerConfig.model}</span>
                </div>
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
            <div>
              Built as a side-project prototype • Model: {providerConfig.model} • Provider: {providerConfig.label} •{' '}
              <a href="https://github.com/Aneesh-382005/Playground" target="_blank" rel="noreferrer">
                GitHub
              </a>
            </div>
            <div className="issue-cta">
              <span className="issue-text">Found an Issue?</span>
              <a
                className="issue-link"
                href="https://github.com/Aneesh-382005/Playground/issues"
                target="_blank"
                rel="noopener noreferrer"
              >
                Raise it here
                <svg width="18" height="18" viewBox="0 0 20 20" fill="none" style={{marginLeft:4,verticalAlign:'middle'}} xmlns="http://www.w3.org/2000/svg">
                  <path d="M7 13L13 7M13 7H7M13 7V13" stroke="#ff7a59" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </a>
            </div>
          </footer>
        </Container>
      </div>
    </>
  );
}

export default App;