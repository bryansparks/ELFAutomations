// File: pages/index.tsx
import type { NextPage } from 'next'
import Head from 'next/head'
import { Box, Typography } from '@mui/material'

const Home: NextPage = () => {
  return (
    <Box>
      <Head>
        <title>AI Marketing Agent</title>
        <meta name="description" content="AI-powered marketing agent for small businesses" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main>
        <Typography variant="h1">
          Welcome to AI Marketing Agent
        </Typography>
      </main>
    </Box>
  )
}

export default Home
