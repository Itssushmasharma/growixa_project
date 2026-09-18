import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // In a real app, you would verify studentId from session token
    // For this clone, we assume we receive it in the body
    
    // Check if the tutor exists and get their price
    const tutorProfile = await prisma.tutorProfile.findUnique({
      where: { userId: body.tutorId }
    });
    
    if (!tutorProfile) {
      return NextResponse.json({ error: "Tutor not found" }, { status: 404 });
    }

    const lesson = await prisma.lesson.create({
      data: {
        studentId: body.studentId,
        tutorId: body.tutorId,
        startTime: new Date(body.startTime),
        endTime: new Date(body.endTime),
        price: tutorProfile.price,
        status: "SCHEDULED"
      }
    });
    
    return NextResponse.json(lesson, { status: 201 });
  } catch (error) {
    console.error("Error booking lesson:", error);
    return NextResponse.json({ error: "Failed to book lesson" }, { status: 500 });
  }
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');
    const role = searchParams.get('role'); // 'STUDENT' or 'TUTOR'
    
    if (!userId) {
      return NextResponse.json({ error: "userId is required" }, { status: 400 });
    }

    let lessons;
    
    if (role === 'TUTOR') {
      lessons = await prisma.lesson.findMany({
        where: { tutorId: userId },
        include: {
          student: { select: { name: true, email: true } }
        },
        orderBy: { startTime: 'asc' }
      });
    } else {
      lessons = await prisma.lesson.findMany({
        where: { studentId: userId },
        include: {
          tutor: { 
            select: { 
              name: true,
              tutorProfile: {
                select: { subject: true, imageUrl: true }
              }
            } 
          }
        },
        orderBy: { startTime: 'asc' }
      });
    }

    return NextResponse.json(lessons);
  } catch (error) {
    console.error("Error fetching lessons:", error);
    return NextResponse.json({ error: "Failed to fetch lessons" }, { status: 500 });
  }
}
