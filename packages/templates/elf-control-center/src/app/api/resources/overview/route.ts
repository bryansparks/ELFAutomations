import { NextRequest, NextResponse } from 'next/server';
import { getServerSupabase } from '@/lib/supabase';

export async function GET(request: NextRequest) {
  try {
    const supabase = getServerSupabase();

    // Get resource state overview
    const { data: overview, error } = await supabase
      .from('resource_state_overview')
      .select('*');

    if (error) {
      console.error('Error fetching resource overview:', error);
      return NextResponse.json(
        { error: 'Failed to fetch resource overview' },
        { status: 500 }
      );
    }

    // Transform data into nested structure
    const transformed: Record<string, Record<string, any>> = {};

    overview.forEach(row => {
      const { resource_type, current_state, count, last_transition } = row;

      if (!transformed[resource_type]) {
        transformed[resource_type] = {};
      }

      transformed[resource_type][current_state] = {
        count,
        last_transition
      };
    });

    return NextResponse.json(transformed);

  } catch (error) {
    console.error('Error in resource overview API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
