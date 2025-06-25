import { NextRequest, NextResponse } from 'next/server';
import { getServerSupabase } from '@/lib/supabase';

export async function GET(request: NextRequest) {
  try {
    const supabase = getServerSupabase();

    // Get resources awaiting action
    const { data: resources, error } = await supabase
      .from('resources_awaiting_action')
      .select('*')
      .limit(20);

    if (error) {
      console.error('Error fetching resources awaiting action:', error);
      return NextResponse.json(
        { error: 'Failed to fetch resources' },
        { status: 500 }
      );
    }

    return NextResponse.json(resources || []);

  } catch (error) {
    console.error('Error in awaiting action API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
