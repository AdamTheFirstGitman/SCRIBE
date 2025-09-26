import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Basic health check for Next.js frontend
    return NextResponse.json(
      {
        status: 'healthy',
        service: 'scribe-frontend',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        environment: process.env.NODE_ENV || 'development'
      },
      { status: 200 }
    )
  } catch (error) {
    return NextResponse.json(
      {
        status: 'unhealthy',
        service: 'scribe-frontend',
        error: 'Health check failed'
      },
      { status: 500 }
    )
  }
}