<?php

namespace Database\Seeders;

use App\Models\Faculty;
use App\Models\User;
// use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        // 1. Buat data master terlebih dahulu.
        $this->call([
            ActivityFieldSeeder::class,
            ActivityTypeSeeder::class,
        ]);

        $this->call([
            FacultyStudyProgramSeeder::class,
            UserSeeder::class,
        ]);

        // Jalankan seeder simulasi hanya di lingkungan development
        if (app()->environment('local')) {
            $this->call(SimulationSeeder::class);
        }
    }
}
