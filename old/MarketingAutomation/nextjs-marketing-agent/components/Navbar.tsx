// File: components/Navbar.tsx
import React from 'react'
import { AppBar, Toolbar, Typography, Button } from '@mui/material'
import Link from 'next/link'

const Navbar: React.FC = () => {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          AI Marketing Agent
        </Typography>
        <Link href="/login" passHref>
          <Button color="inherit">Login</Button>
        </Link>
        <Link href="/register" passHref>
          <Button color="inherit">Register</Button>
        </Link>
      </Toolbar>
    </AppBar>
  )
}

export default Navbar
