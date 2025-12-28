import { LucideIcon } from "lucide-react";

export interface NavItem {
  id: string;
  label: string;
  icon: LucideIcon;
  path: string;
  isNew?: boolean;
}

export interface User {
  username: string;
  avatar: string;
  role: 'admin' | 'user' | 'guest';
}

export interface Playlist {
  id: string;
  title: string;
  curator: string;
  coverUrl: string;
  trackCount: number;
  tags: string[];
}

export interface DiaryEntry {
  id: string;
  title: string;
  excerpt: string;
  author: string;
  date: string;
  mood: 'melancholic' | 'joyful' | 'calm' | 'energetic';
}
