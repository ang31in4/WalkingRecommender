import Foundation
import HealthKit

/// Reads step count from Health (HealthKit). Add HealthKit capability in Xcode and
/// NSHealthShareUsageDescription in Info.plist for step count read.
final class HealthStepService {
    static let shared = HealthStepService()
    private let store = HKHealthStore()

    private init() {}

    private var stepType: HKQuantityType? {
        HKQuantityType.quantityType(forIdentifier: .stepCount)
    }

    /// Request authorization to read step count. Call once (e.g. at app launch or before first read).
    func requestAuthorization() async -> Bool {
        guard let step = stepType else { return false }
        return await withCheckedContinuation { continuation in
            store.requestAuthorization(toShare: [], read: [step]) { granted, _ in
                continuation.resume(returning: granted)
            }
        }
    }

    /// Returns today's step count from Health, or 0 if unavailable/denied.
    func todayStepCount() async -> Int {
        guard let stepType = stepType else { return 0 }
        let calendar = Calendar.current
        let startOfDay = calendar.startOfDay(for: Date())
        let predicate = HKQuery.predicateForSamples(withStart: startOfDay, end: Date(), options: .strictStartDate)
        let sort = [NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)]

        return await withCheckedContinuation { continuation in
            let query = HKSampleQuery(
                sampleType: stepType,
                predicate: predicate,
                limit: HKObjectQueryNoLimit,
                sortDescriptors: sort
            ) { _, samples, error in
                if let error = error {
                    print("[HealthStepService] Step query error: \(error)")
                    continuation.resume(returning: 0)
                    return
                }
                let total = (samples as? [HKQuantitySample])?
                    .reduce(0) { $0 + Int($1.quantity.doubleValue(for: .count())) } ?? 0
                continuation.resume(returning: total)
            }
            store.execute(query)
        }
    }
}
