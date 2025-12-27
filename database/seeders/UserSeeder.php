<?php

namespace Database\Seeders;

use App\Models\Student;
use App\Models\User;
use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class UserSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        // 1. Buat Pengguna Admin
        User::create([
            'name' => 'Admin Kemahasiswaan',
            'email' => 'admin@sinema.fatek.untad.ac.id',
            'password' => Hash::make('Sinema2025'),
            'role' => 'Admin',
            'email_verified_at' => now(),
        ]);

        // // 2. Buat Pengguna Mahasiswa (Student 1) beserta profilnya
        // $studentUser1 = User::create([
        //     'name' => 'Bill Gates',
        //     'email' => 'student1@untad.ac.id',
        //     'password' => Hash::make('password'),
        //     'role' => 'Student',
        // ]);

        // // Kaitkan user mahasiswa dengan profil student
        // Student::create([
        //     'user_id' => $studentUser1->id,
        //     'nim' => 'F55121001',
        //     'faculty_id' => 1,
        //     'study_program_id' => 6,
        // ]);

        // // 3. Buat Pengguna Mahasiswa (Student 2) beserta profilnya
        // $studentUser2 = User::create([
        //     'name' => 'Steve Jobs',
        //     'email' => 'student2@untad.ac.id',
        //     'password' => Hash::make('password'),
        //     'role' => 'Student',
        // ]);

        // // Kaitkan user mahasiswa dengan profil student
        // Student::create([
        //     'user_id' => $studentUser2->id,
        //     'nim' => 'F55221002',
        //     'faculty_id' => 1,
        //     'study_program_id' => 10,
        // ]);
    }
}
