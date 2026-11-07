export interface UserProfile {
  id: number;
  nama: string;
  no_wa: string;
  is_alarm_active: boolean;
  token?: string;
}

export interface FoodCategory {
  id: string;
  title: string;
  type: 'recommended' | 'avoid';
  description: string;
  items: {
    name: string;
    reason: string;
    icon?: string;
  }[];
}

export interface EducationArticle {
  id: 'gastritis' | 'gerd';
  title: string;
  subtitle: string;
  definition: string;
  studentCauses: string[];
  symptoms: string[];
  medicalTips: string[];
}
