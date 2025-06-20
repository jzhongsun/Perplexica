import { ImageResponse } from '@vercel/og';

// Use Node.js runtime instead of Edge runtime for better compatibility
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const size = searchParams.get('size') || '512';
    const maskable = searchParams.get('maskable') === 'true';
    
    const width = parseInt(size);
    const height = width;
    
    // Calculate padding for maskable icons (safe area)
    const padding = maskable ? width * 0.2 : width * 0.1;
    
    return new ImageResponse(
      (
        <div
          style={{
            background: 'linear-gradient(45deg, #000000, #2A2A2A)',
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: `${padding}px`,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '100%',
              height: '100%',
              border: '3px solid #40E0D0',
              borderRadius: '50%',
              position: 'relative',
            }}
          >
            <div
              style={{
                fontSize: `${width * 0.3}px`,
                fontWeight: 'bold',
                background: 'linear-gradient(45deg, #40E0D0, #00CED1)',
                backgroundClip: 'text',
                color: 'transparent',
                textAlign: 'center',
              }}
            >
              AI
            </div>
          </div>
        </div>
      ),
      {
        width,
        height,
      },
    );
  } catch (error) {
    console.error('Error generating icon:', error);
    return new Response('Error generating icon', { status: 500 });
  }
} 