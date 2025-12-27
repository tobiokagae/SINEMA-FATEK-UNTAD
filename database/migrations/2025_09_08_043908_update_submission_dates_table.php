<?php
// File: database/migrations/xxxx_xx_xx_xxxxxx_update_submission_dates_table.php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('submissions', function (Blueprint $table) {
            // 1. Ganti nama kolom activity_date menjadi activity_start_date
            $table->renameColumn('activity_date', 'activity_start_date');

            // 2. Tambahkan kolom baru setelah activity_start_date
            $table->date('activity_end_date')->nullable()->after('activity_start_date');
            $table->date('certificate_date')->nullable()->after('organizer');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('submissions', function (Blueprint $table) {
            $table->renameColumn('activity_start_date', 'activity_date');
            $table->dropColumn(['activity_end_date', 'certificate_date']);
        });
    }
};
