<?php
// File: database/seeders/SimulationSeeder.php

namespace Database\Seeders;

use App\Models\ActivityType;
use App\Models\Faculty;
use App\Models\Student;
use App\Models\Submission;
use App\Models\User;
use Carbon\Carbon;
use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;
use Illuminate\Support\Collection;

class SimulationSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        // Nonaktifkan event model untuk mempercepat proses seeding
        Student::withoutEvents(function () {
            // Ambil semua data master terlebih dahulu untuk efisiensi
            $faculties = Faculty::with('studyPrograms')->get();
            if ($faculties->isEmpty()) {
                $this->call(FacultyStudyProgramSeeder::class);
                $faculties = Faculty::with('studyPrograms')->get();
            }

            $activityTypes = ActivityType::all();
            if ($activityTypes->isEmpty()) {
                $this->call(ActivityTypeSeeder::class);
                $activityTypes = ActivityType::all();
            }

            // Buat 1000 Mahasiswa
            User::factory(1000)->create()->each(function (User $user) use ($faculties) {
                if ($faculties->isNotEmpty()) {
                    $faculty = $faculties->random();
                    $studyProgram = $faculty->studyPrograms->isNotEmpty() ? $faculty->studyPrograms->random() : null;

                    Student::factory()->create([
                        'user_id' => $user->id,
                        'nim' => 'F' . fake()->unique()->numerify('########'),
                        'faculty_id' => $faculty->id,
                        'study_program_id' => $studyProgram?->id,
                    ]);
                }
            });

            $students = Student::all();
            $startDate = Carbon::create(2025, 1, 1);
            $endDate = Carbon::now();

            // Buat Pengajuan untuk setiap Mahasiswa
            foreach ($students as $student) {
                // Setiap mahasiswa akan memiliki 5 s.d. 20 pengajuan
                $submissionCount = rand(5, 20);

                for ($i = 0; $i < $submissionCount; $i++) {
                    $randomStatus = $this->getRandomStatus();
                    $activityDate = fake()->dateTimeBetween($startDate, $endDate);

                    Submission::create([
                        'student_id' => $student->id,
                        'activity_type_id' => $activityTypes->random()->id,
                        'certificate_number' => 'SK/' . rand(100, 999) . '/UN28/' . rand(1, 12) . '/2025',
                        'organizer' => fake()->company(),
                        'certificate_date' => $activityDate,
                        'activity_start_date' => $activityDate,
                        'activity_end_date' => rand(0, 1) ? Carbon::instance($activityDate)->addDays(rand(1, 5)) : null,
                        'proof_document' => 'placeholders/document.pdf',
                        'status' => $randomStatus,
                        'notes' => $randomStatus === 'Rejected' ? 'Bukti tidak sesuai.' : null,
                        'created_at' => $activityDate,
                        'updated_at' => $activityDate,
                    ]);
                }
            }
        });
    }

    /**
     * Mengembalikan status secara acak berdasarkan persentase yang ditentukan.
     */
    private function getRandomStatus(): string
    {
        $rand = rand(1, 100);
        if ($rand <= 80) {
            return 'Verified'; // 80%
        } elseif ($rand <= 95) {
            return 'Submitted'; // 15%
        } else {
            return 'Rejected'; // 5%
        }
    }
}
