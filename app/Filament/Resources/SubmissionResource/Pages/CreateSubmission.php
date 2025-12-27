<?php

namespace App\Filament\Resources\SubmissionResource\Pages;

use App\Filament\Resources\SubmissionResource;
use App\Models\ActivityType;
use Filament\Resources\Pages\CreateRecord;
use Illuminate\Support\Facades\Auth;

class CreateSubmission extends CreateRecord
{
    protected static string $resource = SubmissionResource::class;

    protected function mutateFormDataBeforeCreate(array $data): array
    {
        if (empty($data['activity_type_id'])) {
            $activity = ActivityType::where('activity_field_id', $data['activity_field_id'])
                ->where('name', $data['activity_name'])
                ->whereNull('level')
                ->whereNull('achievement')
                ->first();

            if ($activity) {
                $data['activity_type_id'] = $activity->id;
            }
        }

        // Isi student_id jika yang membuat adalah mahasiswa
        if (Auth::user()?->role === 'Student') {
            $data['student_id'] = Auth::user()->student->id;
        }

        // Hapus field sementara yang tidak ada di database
        unset($data['activity_field_id']);
        unset($data['activity_name']);
        unset($data['activity_level']);

        return $data;
    }
}
