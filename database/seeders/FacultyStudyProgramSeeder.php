<?php
// File: database/seeders/FacultyStudyProgramSeeder.php

namespace Database\Seeders;

use App\Models\Faculty;
use App\Models\Signatory;
use App\Models\StudyProgram;
use Illuminate\Database\Seeder;

class FacultyStudyProgramSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        // Hapus data lama untuk menghindari duplikasi
        Faculty::query()->delete();
        StudyProgram::query()->delete();
        Signatory::query()->delete();

        // Data Fakultas dan Program Studi
        $data = [
            'Teknik' => [
                'programs' => [
                    'S1 Arsitektur',
                    'S1 Teknik Sipil',
                    'S1 Teknik Arsitektur',
                    'S1 Teknik Mesin',
                    'S1 Teknik Elektro',
                    'S1 Teknik Informatika',
                    'S1 Teknik Geologi',
                    'S1 Teknik Lingkungan',
                    'S1 Perencanaan Wilayah dan Kota',
                    'S1 Sistem Informasi',
                    'S1 Teknik Sipil (Kampus Kab. Morowali)',
                    'S1 Teknik Sipil (Kampus Kab. Tojo Una-una)',
                    'D4 Teknologi Rekayasa Instalasi Listrik',
                    'D4 Teknologi Rekayasa Manufaktur',
                    'D4 Teknologi Rekayasa Konstruksi Jalan dan Jembatan'
                ],
                'details' => [
                    'email' => 'fatek@untad.ac.id',
                    'phone' => '0451-422611',
                    'website' => 'https://fatek.untad.ac.id',
                ],
                'signatory' => [
                    'name' => 'Dr. Bakri, ST, Grad.Dipl., M.Phil.',
                    'nip' => '197412121998021001',
                    'pangkat' => 'Pembina Tingkat I',
                    'golongan' => 'IV/b',
                ]
            ],
        ];

        // Looping untuk membuat data
        foreach ($data as $facultyName => $details) {
            // 1. Buat Fakultas dan tambahkan detail kontak
            $faculty = Faculty::create([
                'name' => $facultyName,
                'email' => $details['details']['email'],
                'phone' => $details['details']['phone'],
                'website' => $details['details']['website'],
            ]);

            // 2. Buat Program Studi yang berelasi
            foreach ($details['programs'] as $programName) {
                StudyProgram::create([
                    'faculty_id' => $faculty->id,
                    'name' => $programName,
                ]);
            }

            // 3. Buat Pejabat Penandatangan yang berelasi
            Signatory::create([
                'faculty_id' => $faculty->id,
                'name' => $details['signatory']['name'],
                'nip' => $details['signatory']['nip'],
                'pangkat' => $details['signatory']['pangkat'],
                'golongan' => $details['signatory']['golongan'],
                'jabatan' => 'Wakil Dekan Bidang Kemahasiswaan dan Alumni', // Default
            ]);
        }
    }
}
