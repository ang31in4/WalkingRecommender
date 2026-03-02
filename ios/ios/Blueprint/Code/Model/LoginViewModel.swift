import Foundation
import Combine

class LoginViewModel: ObservableObject {
    @Published var userId: String = ""
    @Published var isLoggedIn: Bool = false
    @Published var errorMessage: String?
    @Published var isLoading: Bool = false

    func login() {
        guard !userId.trimmingCharacters(in: .whitespaces).isEmpty else {
            errorMessage = "Please enter your user ID"
            return
        }

        errorMessage = nil
        isLoading = true

        Task {
            do {
                let success = try await loginRequest(userId: userId.trimmingCharacters(in: .whitespaces))
                await MainActor.run {
                    isLoading = false
                    if success {
                        isLoggedIn = true
                    } else {
                        errorMessage = "User not found"
                    }
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                    errorMessage = error.localizedDescription
                }
            }
        }
    }

    func logout() {
        isLoggedIn = false
        userId = ""
        errorMessage = nil
    }
}
