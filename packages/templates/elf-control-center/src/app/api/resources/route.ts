import { NextRequest, NextResponse } from 'next/server';
import { getServerSupabase } from '@/lib/supabase';

export async function GET(request: NextRequest) {
  try {
    const supabase = getServerSupabase();
    const { searchParams } = new URL(request.url);

    // Build query
    let query = supabase
      .from('resource_states')
      .select('*')
      .order('transitioned_at', { ascending: false });

    // Apply filters
    const resourceType = searchParams.get('type');
    if (resourceType && resourceType !== 'all') {
      query = query.eq('resource_type', resourceType);
    }

    const state = searchParams.get('state');
    if (state && state !== 'all') {
      query = query.eq('current_state', state);
    }

    const search = searchParams.get('search');
    if (search) {
      query = query.ilike('resource_name', `%${search}%`);
    }

    // Execute query
    const { data: resources, error } = await query;

    if (error) {
      console.error('Error fetching resources:', error);
      return NextResponse.json(
        { error: 'Failed to fetch resources' },
        { status: 500 }
      );
    }

    return NextResponse.json(resources || []);

  } catch (error) {
    console.error('Error in resources API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
