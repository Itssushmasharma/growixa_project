import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const subject = searchParams.get('subject');
    const minPrice = searchParams.get('minPrice');
    const maxPrice = searchParams.get('maxPrice');
    const country = searchParams.get('country');

    // Build the query dynamically
    const query: any = {};
    if (subject) query.subject = { contains: subject };
    if (country) query.country = country;
    if (minPrice || maxPrice) {
      query.price = {};
      if (minPrice) query.price.gte = parseFloat(minPrice);
      if (maxPrice) query.price.lte = parseFloat(maxPrice);
    }

    const tutors = await prisma.tutorProfile.findMany({
      where: query,
      include: {
        user: {
          select: { name: true }
        }
      }
    });

    return NextResponse.json(tutors);
  } catch (error) {
    console.error("Error fetching tutors:", error);
    return NextResponse.json({ error: "Failed to fetch tutors" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    // Assuming the user is already authenticated and their userId is known
    // This creates a new tutor profile for an existing user
    const tutorProfile = await prisma.tutorProfile.create({
      data: {
        userId: body.userId,
        headline: body.headline,
        bio: body.bio,
        subject: body.subject,
        country: body.country,
        price: body.price,
        imageUrl: body.imageUrl,
        videoUrl: body.videoUrl
      }
    });
    
    return NextResponse.json(tutorProfile, { status: 201 });
  } catch (error) {
    console.error("Error creating tutor profile:", error);
    return NextResponse.json({ error: "Failed to create tutor profile" }, { status: 500 });
  }
}
